import { useEffect, useState } from "react";

function VoiceSelector() {
  const [voices, setVoices] = useState([]);
  const [current, setCurrent] = useState("");
  const [provider, setProvider] = useState("");
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState(null);

  useEffect(() => {
    fetch("/api/voices")
      .then((res) => {
        if (!res.ok) throw new Error(`Erreur ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setVoices(data.voices || []);
        setCurrent(data.current || "");
        setProvider(data.provider || "");
      })
      .catch(() => setFeedback({ type: "error", text: "Impossible de charger les voix" }))
      .finally(() => setLoading(false));
  }, []);

  const handleChange = async (e) => {
    const voiceId = e.target.value;
    setCurrent(voiceId);
    setFeedback(null);
    try {
      const res = await fetch("/api/voice", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice_id: voiceId }),
      });
      if (!res.ok) throw new Error(`Erreur ${res.status}`);
      setFeedback({ type: "success", text: "Voix mise a jour" });
      setTimeout(() => setFeedback(null), 2000);
    } catch (err) {
      setFeedback({ type: "error", text: "Erreur : " + err.message });
    }
  };

  if (loading) return null;

  const providerLabel = provider === "elevenlabs" ? "ElevenLabs" : "Edge TTS";

  return (
    <div className="voice-selector">
      <h3>Voix</h3>
      <p className="voice-provider">Provider : {providerLabel}</p>
      <select value={current} onChange={handleChange}>
        {voices.map((v) => (
          <option key={v.id} value={v.id}>
            {v.name}
          </option>
        ))}
      </select>
      {feedback && (
        <p className={`voice-feedback ${feedback.type}`}>{feedback.text}</p>
      )}
    </div>
  );
}

export default VoiceSelector;
