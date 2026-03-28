import { useState } from "react";

function MessageCard({ message, audioVersion, onSave }) {
  const [text, setText] = useState(message.text);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

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

  // Synchroniser le texte quand le message parent change (apres sauvegarde)
  const currentText = isModified ? text : message.text;

  return (
    <div className="message-card">
      <div>
        <h3>
          {message.label}
          {message.has_music && <span className="badge">Musique</span>}
        </h3>
        <p className="description">{message.description}</p>
      </div>

      <textarea
        value={currentText}
        onChange={(e) => setText(e.target.value)}
        rows={4}
      />

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
    </div>
  );
}

export default MessageCard;
