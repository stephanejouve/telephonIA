import AppKit
import WebKit

// MARK: - Application Delegate

class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var backendProcess: Process?
    var backendPort: Int?
    private var retryTimer: Timer?
    private var retryCount = 0
    private let maxRetries = 60  // 30 secondes max (60 * 500ms)

    func applicationDidFinishLaunching(_ notification: Notification) {
        startBackend()
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }

    func applicationWillTerminate(_ notification: Notification) {
        stopBackend()
    }

    // MARK: - Backend Management

    private func startBackend() {
        let bundle = Bundle.main
        let resourcePath = bundle.resourcePath ?? bundle.bundlePath
        let backendDir = (resourcePath as NSString).appendingPathComponent("python_backend")
        let backendExe = (backendDir as NSString).appendingPathComponent("telephonia-web")

        guard FileManager.default.fileExists(atPath: backendExe) else {
            showError("Backend introuvable: \(backendExe)")
            return
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: backendExe)
        process.currentDirectoryURL = URL(fileURLWithPath: backendDir)
        process.environment = ProcessInfo.processInfo.environment
        process.environment?["TELEPHONIA_APP_MODE"] = "1"

        let pipe = Pipe()
        process.standardOutput = pipe

        process.launch()

        backendProcess = process

        // Lire stdout dans un thread separe pour trouver PORT:XXXXX
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            let handle = pipe.fileHandleForReading
            let data = NSMutableData()

            while true {
                let chunk = handle.availableData
                if chunk.isEmpty { break }
                data.append(chunk)

                if let output = String(data: data as Data, encoding: .utf8),
                   let range = output.range(of: "PORT:(\\d+)", options: .regularExpression) {
                    let portStr = output[range].dropFirst(5)  // Enlever "PORT:"
                    if let port = Int(portStr) {
                        DispatchQueue.main.async {
                            self?.backendPort = port
                            self?.createWindow(port: port)
                        }
                        // Continuer a drainer stdout sans bloquer
                        while !handle.availableData.isEmpty {}
                        return
                    }
                }
            }

            // Si on arrive ici, le process s'est termine sans PORT
            DispatchQueue.main.async {
                self?.showError("Le backend s'est termine sans communiquer de port.")
            }
        }
    }

    private func stopBackend() {
        retryTimer?.invalidate()
        retryTimer = nil

        if let process = backendProcess, process.isRunning {
            process.terminate()  // SIGTERM
            // Attendre un peu, puis forcer si necessaire
            DispatchQueue.global().asyncAfter(deadline: .now() + 2.0) {
                if process.isRunning {
                    process.interrupt()  // SIGINT
                }
            }
        }
        backendProcess = nil
    }

    // MARK: - Window & WebView

    private func createWindow(port: Int) {
        let config = WKWebViewConfiguration()
        config.preferences.setValue(true, forKey: "developerExtrasEnabled")

        webView = WKWebView(frame: .zero, configuration: config)
        webView.uiDelegate = self
        webView.navigationDelegate = self

        let windowRect = NSRect(x: 0, y: 0, width: 1024, height: 768)
        window = NSWindow(
            contentRect: windowRect,
            styleMask: [.titled, .closable, .resizable, .miniaturizable],
            backing: .buffered,
            defer: false
        )
        window.title = "telephonIA"
        window.contentView = webView
        window.center()
        window.makeKeyAndOrderFront(nil)

        loadURL(port: port)
    }

    private func loadURL(port: Int) {
        guard let url = URL(string: "http://localhost:\(port)") else { return }
        let request = URLRequest(url: url)
        webView.load(request)
    }

    // MARK: - Error Display

    private func showError(_ message: String) {
        let alert = NSAlert()
        alert.messageText = "Erreur telephonIA"
        alert.informativeText = message
        alert.alertStyle = .critical
        alert.addButton(withTitle: "Quitter")
        alert.runModal()
        NSApp.terminate(nil)
    }
}

// MARK: - WKUIDelegate (alert, confirm, prompt JavaScript)

extension AppDelegate: WKUIDelegate {
    func webView(
        _ webView: WKWebView,
        runJavaScriptAlertPanelWithMessage message: String,
        initiatedByFrame frame: WKFrameInfo,
        completionHandler: @escaping () -> Void
    ) {
        let alert = NSAlert()
        alert.messageText = "telephonIA"
        alert.informativeText = message
        alert.addButton(withTitle: "OK")
        alert.runModal()
        completionHandler()
    }

    func webView(
        _ webView: WKWebView,
        runJavaScriptConfirmPanelWithMessage message: String,
        initiatedByFrame frame: WKFrameInfo,
        completionHandler: @escaping (Bool) -> Void
    ) {
        let alert = NSAlert()
        alert.messageText = "telephonIA"
        alert.informativeText = message
        alert.addButton(withTitle: "OK")
        alert.addButton(withTitle: "Annuler")
        let response = alert.runModal()
        completionHandler(response == .alertFirstButtonReturn)
    }

    func webView(
        _ webView: WKWebView,
        runJavaScriptTextInputPanelWithPrompt prompt: String,
        defaultText: String?,
        initiatedByFrame frame: WKFrameInfo,
        completionHandler: @escaping (String?) -> Void
    ) {
        let alert = NSAlert()
        alert.messageText = "telephonIA"
        alert.informativeText = prompt
        alert.addButton(withTitle: "OK")
        alert.addButton(withTitle: "Annuler")

        let textField = NSTextField(frame: NSRect(x: 0, y: 0, width: 300, height: 24))
        textField.stringValue = defaultText ?? ""
        alert.accessoryView = textField

        let response = alert.runModal()
        if response == .alertFirstButtonReturn {
            completionHandler(textField.stringValue)
        } else {
            completionHandler(nil)
        }
    }
}

// MARK: - WKNavigationDelegate (retry si serveur pas pret)

extension AppDelegate: WKNavigationDelegate {
    func webView(
        _ webView: WKWebView,
        didFail navigation: WKNavigation!,
        withError error: Error
    ) {
        retryLoadIfNeeded()
    }

    func webView(
        _ webView: WKWebView,
        didFailProvisionalNavigation navigation: WKNavigation!,
        withError error: Error
    ) {
        retryLoadIfNeeded()
    }

    private func retryLoadIfNeeded() {
        guard retryCount < maxRetries, let port = backendPort else {
            showError("Impossible de se connecter au backend apres \(retryCount) tentatives.")
            return
        }
        retryCount += 1
        retryTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: false) { [weak self] _ in
            self?.loadURL(port: port)
        }
    }
}

// MARK: - Entry Point

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
