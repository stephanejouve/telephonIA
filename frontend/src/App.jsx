import { useEffect, useState } from "react";
import GenerateButton from "./components/GenerateButton";
import Header from "./components/Header";
import MessageCard from "./components/MessageCard";
import MusicUpload from "./components/MusicUpload";

function App() {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [audioVersion, setAudioVersion] = useState(0);

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
        />
      ))}
      <MusicUpload />
      {messages.length > 0 && (
        <GenerateButton onGenerate={handleGenerate} />
      )}
    </div>
  );
}

export default App;
