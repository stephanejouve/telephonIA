import { useRef, useState } from "react";

function MessageCard({ message, audioVersion, onSave, onAudioImport, onAudioDelete }) {
  const [text, setText] = useState(message.text);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);
  const [importStatus, setImportStatus] = useState(null);
  const [importing, setImporting] = useState(false);
  const [audioImported, setAudioImported] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const fileInputRef = useRef(null);

  const isModified = text !== message.text;

  const handleSave = async () => {
    setSaving(true);
    setSaveStatus(null);
    try {
      await onSave(message.name, text);
      setSaveStatus("ok");
      setTimeout(() => setSaveStatus(null), 2000);
    } catch (err) {
      setSaveStatus("error");
    } finally {
      setSaving(false);
    }
  };

  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setImporting(true);
    setImportStatus(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`/api/audio/${message.name}/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || `Erreur ${res.status}`);
      }
      setImportStatus("ok");
      setAudioImported(true);
      setTimeout(() => setImportStatus(null), 2000);
      onAudioImport();
    } catch (err) {
      setImportStatus("error");
      setTimeout(() => setImportStatus(null), 3000);
    } finally {
      setImporting(false);
      fileInputRef.current.value = "";
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      const res = await fetch(`/api/audio/${message.name}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error(`Erreur ${res.status}`);
      setAudioImported(false);
      onAudioDelete();
    } catch {
      // silencieux
    } finally {
      setDeleting(false);
    }
  };

  // Synchroniser le texte quand le message parent change (apres sauvegarde)
  const currentText = isModified ? text : message.text;

  return (
    <div className="message-card">
      <div>
        <h3>
          {message.label}
          {message.has_music && (
            <span className={`badge${message.imported_g729 ? " badge-disabled" : ""}`}>
              Musique{message.imported_g729 ? " (non mixee)" : ""}
            </span>
          )}
        </h3>
        <p className="description">{message.description}</p>
      </div>

      <div className="textarea-wrapper">
        <textarea
          value={currentText}
          onChange={(e) => {
            setText(e.target.value);
            setAudioImported(false);
          }}
          rows={4}
          className={audioImported ? "imported" : ""}
        />
        {audioImported && (
          <span className="textarea-watermark">
            Audio importe — texte non utilise
          </span>
        )}
      </div>

      <div className="actions">
        <button
          className="btn-save"
          onClick={handleSave}
          disabled={!isModified || saving}
        >
          {saving ? "Sauvegarde..." : "Sauvegarder"}
        </button>
        {isModified && (
          <span className="modified-indicator">Modifie</span>
        )}
        {saveStatus === "ok" && (
          <span className="save-ok">Sauvegarde !</span>
        )}
        {saveStatus === "error" && (
          <span className="generate-result error">Erreur</span>
        )}
      </div>

      {message.has_audio ? (
        <div className="audio-player">
          <audio
            controls
            src={`/api/audio/${message.name}?v=${audioVersion}`}
            key={audioVersion}
          />
        </div>
      ) : (
        <p className="no-audio">Aucun audio genere</p>
      )}

      <div className="audio-import">
        <input
          type="file"
          accept="audio/*"
          ref={fileInputRef}
          onChange={handleImport}
          style={{ display: "none" }}
        />
        <button
          className="btn-import"
          onClick={() => fileInputRef.current.click()}
          disabled={importing}
        >
          {importing ? "Import en cours..." : "Importer audio"}
        </button>
        {message.has_audio && (
          <>
            <a
              className="link-download"
              href={`/api/audio/${message.name}?v=${audioVersion}`}
              download={`${message.name}.wav`}
            >
              Telecharger
            </a>
            <button
              className="btn-delete-audio"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? "Suppression..." : "Supprimer"}
            </button>
          </>
        )}
        {importStatus === "ok" && (
          <span className="save-ok">Audio importe !</span>
        )}
        {importStatus === "error" && (
          <span className="generate-result error">Erreur d'import</span>
        )}
      </div>
    </div>
  );
}

export default MessageCard;
