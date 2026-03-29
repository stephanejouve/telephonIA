import { useEffect, useState } from "react";
import GenerateButton from "./components/GenerateButton";
import Header from "./components/Header";
import MessageCard from "./components/MessageCard";
import MusicUpload from "./components/MusicUpload";
import VoiceSelector from "./components/VoiceSelector";

function App() {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [audioVersion, setAudioVersion] = useState(0);
  const [serverDown, setServerDown] = useState(false);

  const fetchMessages = async () => {
    try {
      const res = await fetch("/api/messages");
      if (!res.ok) throw new Error(`Erreur ${res.status}`);
      const data = await res.json();
      setMessages(data);
      setError(null);
    } catch (err) {
      setError("Impossible de charger les messages : " + err.message);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, []);

  // Health check : detecter l'arret du serveur
  useEffect(() => {
    let failures = 0;
    const interval = setInterval(async () => {
      try {
        const res = await fetch("/api/health");
        if (res.ok) failures = 0;
        else failures++;
      } catch {
        failures++;
      }
      if (failures >= 2) {
        setServerDown(true);
        clearInterval(interval);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSave = async (name, text) => {
    const res = await fetch(`/api/messages/${name}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error(`Erreur ${res.status}`);
    const updated = await res.json();
    setMessages((prev) =>
      prev.map((m) => (m.name === name ? updated : m))
    );
  };

  const handleAudioImport = () => {
    setAudioVersion((v) => v + 1);
    fetchMessages();
  };

  const handleAudioDelete = () => {
    fetchMessages();
  };

  const handleGenerate = async () => {
    const res = await fetch("/api/generate", { method: "POST" });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(detail);
    }
    const data = await res.json();
    setAudioVersion((v) => v + 1);
    await fetchMessages();
    return data;
  };

  if (serverDown) {
    return (
      <div className="shutdown-screen">
        <div className="shutdown-card">
          <h1>telephonIA</h1>
          <p>L'application a ete fermee.</p>
          <p className="shutdown-hint">Vous pouvez fermer cet onglet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header />
      {error && <div className="error-banner">{error}</div>}
      {messages.map((msg) => (
        <MessageCard
          key={msg.name}
          message={msg}
          audioVersion={audioVersion}
          onSave={handleSave}
          onAudioImport={handleAudioImport}
          onAudioDelete={handleAudioDelete}
        />
      ))}
      <MusicUpload />
      <VoiceSelector />
      {messages.length > 0 && (
        <GenerateButton onGenerate={handleGenerate} />
      )}
    </div>
  );
}

export default App;
