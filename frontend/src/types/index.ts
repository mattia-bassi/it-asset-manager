export interface Person {
  id: number;
  first_name: string;
  last_name: string;
  site_id: number | null;
  site_name: string | null;
  email: string | null;
  extension: string | null;
  mobile_phone: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  linked_username: string | null;
}

export interface Site {
  id: number;
  name: string;
  address: string | null;
  city: string | null;
  postal_code: string | null;
  country: string | null;
  centralino: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AssetType {
  id: number;
  name: string;
  parent_id: number | null;
  parent_name?: string | null;
  description?: string | null;
  fields_schema: Record<string, string> | null;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  children?: AssetType[];
}

export interface Asset {
  id: number;
  asset_code: string | null;
  serial_number: string;
  mac_address: string | null;
  asset_type_id: number;
  manufacturer: string;
  model: string;
  site_id: number | null;
  person_id: number | null;
  location_id?: number | null;
  status: string;
  purchase_date: string | null;
  warranty_expiry: string | null;
  specifications: Record<string, any> | null;
  notes: string | null;
  is_active: boolean;
  asset_type_name: string;
  site_name: string | null;
  person_name: string | null;
  location_name?: string | null;
}

export interface Badge {
  id: number;
  numero_badge: string;
  tipo: 'dipendente' | 'visitatore' | 'temporaneo';
  status: 'attivo' | 'disattivo' | 'smarrito';
  data_emissione: string;
  data_scadenza: string | null;
  site_id: number | null;
  person_id: number | null;
  person_first_name: string | null;
  person_last_name: string | null;
  site_name: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Sim {
  id: number;
  seriale: string;
  operatore: string;
  site_id: number | null;
  numero_telefono: string;
  person_id: number | null;
  person_first_name: string | null;
  person_last_name: string | null;
  status: 'disponibile' | 'assegnata' | 'disattivata';
  is_active?: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface InventorySku {
  id: number;
  category: string;
  device: string;
  brand: string | null;
  quantity: number;
}

export interface AssignmentItem {
  id: number;
  item_type: string;
  asset_id: number | null;
  inventory_sku_id: number | null;
  sim_id: number | null;
  quantity: number;
  item_description: string;
}

export interface Assignment {
  id: number;
  person_id: number;
  assignment_date: string;
  return_date: string | null;
  assignment_type: string;
  status: string;
  notes: string | null;
  is_active: boolean;
  assignment_number: string;
  person_name: string;
  person_email: string | null;
  creator_name: string | null;
  items: AssignmentItem[];
}

export interface Supplier {
  id: number;
  name: string;
  contact_person?: string | null;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
  contract_number?: string | null;
  warranty_conditions?: string | null;
  warranty_duration_months?: number | null;
  notes?: string | null;
  is_active: boolean;
  created_at?: string | null;
}

export interface SupplierListResponse {
  items: Supplier[];
  total: number;
}

export interface Document {
  id: number;
  name: string;
  description?: string;
  category: string;
  filename: string;
  file_size: number;
  mime_type: string;
  uploaded_by?: number;
  uploader_username?: string;
  is_active: boolean;
  created_at: string;
}

export interface DocumentListResponse {
  items: Document[];
  total: number;
}
