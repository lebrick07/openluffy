import { useEffect, useState } from "react";
import "./App.css";

export default function App() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("/api/")
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData({ error: "backend not reachable" }));
  }, []);

  return (
    <>
      <h1>openbrick-playground</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </>
  );
}
