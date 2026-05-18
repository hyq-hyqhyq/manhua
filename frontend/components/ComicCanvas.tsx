import { assetUrl } from "@/lib/api";

type Props = {
  imagePath: string;
};

export default function ComicCanvas({ imagePath }: Props) {
  return (
    <section className="comic-canvas">
      <div className="section-heading compact">
        <p className="eyebrow">Final comic</p>
        <h2>Composited page</h2>
      </div>
      <img src={assetUrl(imagePath)} alt="Final mock comic page" />
    </section>
  );
}
