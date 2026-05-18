import CreateComicForm from "@/components/CreateComicForm";

export default function HomePage() {
  return (
    <main className="page-shell create-page">
      <section className="create-panel">
        <div className="section-heading">
          <p className="eyebrow">Entity Pool Comic Lab</p>
          <h1>Generate a mock multi-panel comic</h1>
        </div>
        <CreateComicForm />
      </section>
    </main>
  );
}
