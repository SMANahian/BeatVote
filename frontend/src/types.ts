export type MeResponse =
  | { authenticated: true; user: { id: string; username: string } }
  | { authenticated: false; guest: { id: string | null; name: string | null } };

export type Room = {
  _id: string;
  name: string;
  active: boolean;
  role: "host" | "suggestor" | "listener" | null;
  code_listener?: string;
  code_suggestor?: string;
  host_token?: string;
};

export type Song = {
  _id: string;
  room_id: string;
  video_id: string;
  title: string;
  thumbnail_url?: string | null;
  duration_sec?: number | null;
  added_by_display_name?: string | null;
  added_at?: string | null;
  score: number;
  my_vote: "like" | "dislike" | null;
  played: boolean;
  removed_by_host: boolean;
  removed_at?: string | null;
};

export type QueueResponse = {
  queue: Song[];
  current_song_id: string | null;
};

export type YoutubeResult = {
  video_id: string;
  title: string;
  channel: string;
  duration: string;
  duration_sec: number;
  thumbnail_url: string;
};

export type ChatMessage = {
  _id: string;
  sender_name: string;
  message: string;
  created_at: string | null;
};

