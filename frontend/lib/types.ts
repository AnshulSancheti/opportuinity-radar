export interface Paginated<T> {
  items: T[];
  limit: number;
  offset: number;
  total: number;
}

export interface Article {
  id: number;
  title: string;
  url: string | null;
  source_name: string;
  author: string | null;
  published_at: string | null;
  summary: string | null;
  category: string;
  tags: string[];
  score: number | null;
  image_url: string | null;
}

export interface Job {
  id: number;
  title: string;
  company: string;
  location: string | null;
  remote_type: string | null;
  employment_type: string | null;
  skills: string[];
  apply_url: string | null;
  source_name: string;
  date_posted: string | null;
  status: string;
}

export interface Hackathon {
  id: number;
  name: string;
  organizer: string | null;
  url: string | null;
  source_name: string;
  mode: string | null;
  location: string | null;
  registration_deadline: string | null;
  start_date: string | null;
  end_date: string | null;
  prize_text: string | null;
  themes: string[];
  status: string;
}

export interface Stats {
  total_jobs: number;
  total_articles: number;
  total_hackathons: number;
  last_scrape_at: string | null;
  failed_sources: number;
  active_scrapes: string[];
}

export interface UserAction {
  id: number;
  item_type: string;
  item_id: number;
  action: string;
  created_at: string;
}

export interface ScrapeRun {
  id: number;
  source_name: string;
  module: string;
  status: string;
  items_found: number;
  items_inserted: number;
  items_updated: number;
  items_skipped: number;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
}
