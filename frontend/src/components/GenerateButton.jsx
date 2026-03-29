import { useState } from "react";

function GenerateButton({ onGenerate }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleClick = async () => {
    setLoading(true);
    setResult(null);
    try {
      const data = await onGenerate();
      if (!data) return;
      setResult({
        type: "success",
        text: `${data.results.length} messages generes avec succes`,
      });
    } catch (err) {
      setResult({
        type: "error",
        text: "Erreur : " + err.message,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="generate-section">
      <button
        className="btn-generate"
        onClick={handleClick}
        disabled={loading}
      >
        {loading && <span className="spinner" />}
        {loading ? "Generation en cours..." : "Generer les messages"}
      </button>
      {result && (
        <p className={`generate-result ${result.type}`}>{result.text}</p>
      )}
    </div>
  );
}

export default GenerateButton;
