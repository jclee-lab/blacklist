export interface SchemaTable {
  name: string;
  column_count: number;
  row_count: number;
}

export interface TableColumn {
  name: string;
  type: string;
  nullable: boolean;
  default_value?: string;
}

export interface TableDetails {
  name: string;
  columns: TableColumn[];
  record_count: number;
}
