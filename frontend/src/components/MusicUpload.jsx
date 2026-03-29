import { useEffect, useRef, useState } from "react";

function MusicUpload() {
  const [hasMusic, setHasMusic] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState(null);
  const fileRef = useRef(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/music");
      if (res.ok) {
        const data = await res.json();
        setHasMusic(data.has_music);
      }
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleUpload = async () => {
    const file = fileRef.current?.files[0];
    if (!file) return;

    setUploading(true);
    setStatus(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/api/music", { method: "POST", body: form });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || `Erreur ${res.status}`);
      }
      setHasMusic(true);
      setStatus({ type: "success", text: "Musique uploadee" });
      fileRef.current.value = "";
    } catch (err) {
      setStatus({ type: "error", text: err.message });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Supprimer la musique de fond ?")) return;
    try {
      const res = await fetch("/api/music", { method: "DELETE" });
      if (res.ok) {
        const data = await res.json();
        setHasMusic(data.has_music);
        setStatus({ type: "success", text: "Musique supprimee" });
      }
    } catch (err) {
      setStatus({ type: "error", text: err.message });
    }
  };

  return (
    <div className="music-upload">
      <h3>Musique de fond</h3>
      <p className="music-status">
        {hasMusic ? "Musique de fond active" : "Aucune musique de fond"}
      </p>
      <div className="music-actions">
        <input
          ref={fileRef}
          type="file"
          accept=".mp3,audio/mpeg"
          className="music-file-input"
        />
        <button
          className="btn-upload"
          onClick={handleUpload}
          disabled={uploading}
        >
          {uploading ? "Upload..." : "Uploader"}
        </button>
        {hasMusic && (
          <button className="btn-delete-music" onClick={handleDelete}>
            Supprimer
          </button>
        )}
      </div>
      {status && (
        <p className={`music-feedback ${status.type}`}>{status.text}</p>
      )}
    </div>
  );
}

export default MusicUpload;
