export type LayoutName = "1x4" | "2x2" | "2x3" | "3x3";

export type StyleName =
  | "black_white_manga"
  | "color_webtoon"
  | "american_comic"
  | "children_book"
  | "cinematic_comic";

export type ComicCreateRequest = {
  user_prompt: string;
  layout: LayoutName;
  style: StyleName;
};

export type ComicCreateResponse = {
  comic_id: string;
  status: string;
};

export type ComicStatus = {
  status: string;
  current_panel: number;
  total_panels: number;
  message: string;
  warnings: string[];
  provider_status: Record<string, string>;
};

export type StoryboardEntity = {
  entity_id: string;
  description: string;
};

export type PanelTextType = "speech" | "thought" | "caption" | "sfx";

export type PanelTextPosition =
  | "top_left"
  | "top_center"
  | "top_right"
  | "middle_left"
  | "middle_right"
  | "bottom_left"
  | "bottom_center"
  | "bottom_right";

export type PanelTextItem = {
  type: PanelTextType;
  speaker: string | null;
  content: string;
  position: PanelTextPosition;
};

export type StoryboardPanel = {
  panel_id: number;
  summary: string;
  entities_used: string[];
  text: PanelTextItem[];
};

export type Storyboard = {
  style: StyleName;
  layout: LayoutName;
  entities: StoryboardEntity[];
  panels: StoryboardPanel[];
};

export type Panel = {
  panel_id: number;
  image_path: string;
  summary: string;
  text: PanelTextItem[];
  reference_sheet_path: string;
};

export type EntityRef = {
  ref_id: string;
  rgba_path: string;
  source: string;
  note: string;
};

export type EntityPoolItem = {
  description: string;
  refs: EntityRef[];
};

export type EntityPool = Record<string, EntityPoolItem>;

export type ComicResult = {
  comic_id: string;
  status: string;
  storyboard: Storyboard;
  comic_page: string;
  panels: Panel[];
  entity_pool: EntityPool;
  warnings: string[];
  provider_status: Record<string, string>;
};

export type RevisionPlan = {
  revision_type: "global" | "panel";
  affected_panels: number[];
  regenerate_mode: "affected_panels" | "selected_only" | "from_panel_k";
  panel_revisions: {
    panel_id: number;
    new_summary: string;
    new_text: PanelTextItem[];
  }[];
};

export type RevisionResponse = {
  comic_id: string;
  status: string;
  revision_plan: RevisionPlan;
};
