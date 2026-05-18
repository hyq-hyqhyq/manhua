import { assetUrl } from "@/lib/api";

type Props = {
  path: string;
  panelId: number;
};

export default function ReferenceSheetViewer({ path, panelId }: Props) {
  return (
    <div className="reference-sheet">
      <p>Reference sheet</p>
      <img src={assetUrl(path)} alt={`Reference sheet for panel ${panelId}`} />
    </div>
  );
}
