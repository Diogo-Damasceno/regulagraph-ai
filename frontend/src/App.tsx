import { useEffect, useState } from "react";
import { Activity, BookOpen, Network, Search, ShieldCheck, Upload } from "lucide-react";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
type Norm = { id: string; title: string; agency: string; status: string; effective_from?: string };
type Evidence = { title: string; provision: string; page: number; quote: string; score: number };

export function App() {
  const [norms, setNorms] = useState<Norm[]>([]);
  const [question, setQuestion] = useState("");
  const [referenceDate, setReferenceDate] = useState("");
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [answer, setAnswer] = useState("Faça uma pergunta sobre as normas vigentes.");

  const load = () => fetch(`${API}/norms`).then(r => r.json()).then(setNorms).catch(() => setNorms([]));
  useEffect(() => { load(); }, []);

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    const response = await fetch(`${API}/questions`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({question, reference_date: referenceDate || null})});
    const data = await response.json(); setAnswer(data.answer); setEvidence(data.evidence ?? []);
  }

  async function upload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const body = new FormData(e.currentTarget);
    await fetch(`${API}/norms/upload`, {method: "POST", body});
    e.currentTarget.reset(); setTimeout(load, 600);
  }

  return <div className="shell">
    <aside><div className="brand"><ShieldCheck/> RegulaGraph <b>AI</b></div>
      <nav><span className="active"><Activity/>Visão geral</span><span><BookOpen/>Normas</span><span><Network/>Grafo</span><span><Search/>Pesquisa temporal</span></nav>
      <small>Inteligência regulatória<br/>com evidências verificáveis.</small>
    </aside>
    <main>
      <header><div><p className="eyebrow">PAINEL REGULATÓRIO</p><h1>Conhecimento normativo, conectado.</h1></div><span className="online">● pipeline online</span></header>
      <section className="metrics">
        <article><label>Normas indexadas</label><strong>{norms.length}</strong><p>Documentos no acervo</p></article>
        <article><label>Em processamento</label><strong>{norms.filter(n => n.status !== "completed").length}</strong><p>Fila assíncrona</p></article>
        <article><label>Fontes</label><strong>{new Set(norms.map(n => n.agency)).size}</strong><p>Órgãos monitorados</p></article>
      </section>
      <div className="grid">
        <section className="panel"><div className="panelTitle"><Upload/><div><h2>Ingerir documento</h2><p>PDF público com texto pesquisável</p></div></div>
          <form onSubmit={upload} className="upload"><input name="title" placeholder="Título da norma" required/><input name="agency" placeholder="Órgão (ex.: ANEEL)" required/><input name="effective_from" type="date"/><input name="file" type="file" accept="application/pdf" required/><button>Processar norma</button></form>
        </section>
        <section className="panel"><div className="panelTitle"><Search/><div><h2>Consulta temporal</h2><p>Respostas limitadas à vigência escolhida</p></div></div>
          <form onSubmit={ask} className="ask"><textarea value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Quais obrigações se aplicavam às distribuidoras?" required/><div><input type="date" value={referenceDate} onChange={e=>setReferenceDate(e.target.value)}/><button>Pesquisar</button></div></form>
        </section>
      </div>
      <section className="panel result"><h2>Resposta rastreável</h2><p>{answer}</p>{evidence.map((item, i)=><article key={i}><b>{item.title} · {item.provision} · pág. {item.page}</b><blockquote>{item.quote}</blockquote><small>relevância lexical: {item.score}</small></article>)}</section>
      <section className="panel"><h2>Documentos recentes</h2><div className="table"><div className="row head"><span>Norma</span><span>Órgão</span><span>Vigência</span><span>Status</span></div>{norms.map(n=><div className="row" key={n.id}><span>{n.title}</span><span>{n.agency}</span><span>{n.effective_from ?? "—"}</span><span className="status">{n.status}</span></div>)}</div></section>
    </main>
  </div>;
}
