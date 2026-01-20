'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { Table2, FileJson, RefreshCw, ChevronLeft, ChevronRight, Loader2, AlertCircle } from 'lucide-react';
import { getDatabaseSchema, getDatabaseTableData } from '@/lib/api';
import { SchemaTable } from './types';

const PAGE_SIZE = 50;

interface TableDataResponse {
  rows: Record<string, unknown>[];
  columns: string[];
  pagination: {
    total: number;
    total_pages: number;
    current_page: number;
    per_page: number;
  };
}

export default function TableBrowserClient() {
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(1);

  // 1. Schema Query
  const { 
    data: tables = [], 
    isLoading: isSchemaLoading,
    isError: isSchemaError,
    error: schemaError 
  } = useQuery({
    queryKey: ['database-schema'],
    queryFn: async () => {
      const payload = await getDatabaseSchema();
      const rawData = payload?.data?.schema ?? payload?.data ?? payload?.schema ?? payload;
      
      if (Array.isArray(rawData)) {
        return rawData as SchemaTable[];
      }
      
      if (rawData?.tables && Array.isArray(rawData.tables)) {
        return rawData.tables as SchemaTable[];
      }
      
      if (typeof rawData === 'object' && rawData !== null) {
        return Object.entries(rawData).map(([name, info]) => ({
          name,
          column_count: Array.isArray(info) ? info.length : (info as { columns?: unknown[] })?.columns?.length ?? 0,
          row_count: (info as { record_count?: number })?.record_count ?? 0,
        })) as SchemaTable[];
      }
      
      return [];
    },
    staleTime: 5 * 60 * 1000,
  });

  // Auto-select first table
  useEffect(() => {
    if (!selectedTable && tables.length > 0) {
      setSelectedTable(tables[0].name);
    }
  }, [tables, selectedTable]);

  // 2. Data Query
  const { 
    data: tableData, 
    isLoading: isTableLoading, 
    isFetching: isTableFetching,
    isError: isTableError,
    error: tableError,
    refetch: refetchTableData 
  } = useQuery({
    queryKey: ['table-data', selectedTable, currentPage],
    queryFn: async () => {
      if (!selectedTable) return null;
      const payload = await getDatabaseTableData(selectedTable, `page=${currentPage}&limit=${PAGE_SIZE}`);
      return (payload?.data ?? payload) as TableDataResponse;
    },
    enabled: !!selectedTable,
    placeholderData: keepPreviousData,
    staleTime: 1 * 60 * 1000, // 1 minute
  });

  const handleTableChange = (tableName: string) => {
    setSelectedTable(tableName);
    setCurrentPage(1);
  };

  const rows = useMemo(() => tableData?.rows ?? [], [tableData]);
  
  // Use explicit columns if available, otherwise derive from first row
  const columns = useMemo(() => {
    if (tableData?.columns?.length) return tableData.columns;
    if (rows.length > 0) return Object.keys(rows[0]);
    return [];
  }, [tableData?.columns, rows]);

  const pagination = tableData?.pagination ?? { total: 0, total_pages: 0 };
  const totalRows = pagination.total || rows.length;
  const totalPages = pagination.total_pages || (totalRows > 0 ? Math.ceil(totalRows / PAGE_SIZE) : 0);

  // Cell formatter to avoid repeated JSON.stringify in render loop
  const formatCell = useCallback((value: unknown): { text: string; fullText: string } => {
    if (typeof value === 'object' && value !== null) {
      const stringified = JSON.stringify(value, null, 2);
      // Compact version for display
      const compact = JSON.stringify(value); 
      return { 
        text: compact.length > 100 ? compact.substring(0, 100) + '...' : compact,
        fullText: stringified 
      };
    }
    const str = String(value ?? '');
    return { text: str, fullText: str };
  }, []);

  const isLoading = isSchemaLoading || (isTableLoading && !tableData);

  // Error State for Schema
  if (isSchemaError) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg flex items-center border border-red-200">
        <AlertCircle className="h-5 w-5 mr-2" />
        <span>스키마를 불러오는데 실패했습니다: {(schemaError as Error).message}</span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Sidebar */}
      <div className="lg:col-span-1">
        <div className="bg-white rounded-lg shadow p-4 sticky top-8 max-h-[calc(100vh-100px)] overflow-hidden flex flex-col">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2 flex-shrink-0">
            <Table2 className="h-5 w-5" />
            테이블 목록
          </h2>
          
          {isSchemaLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : (
            <div className="space-y-2 overflow-y-auto custom-scrollbar flex-1 pr-1">
              {tables.length > 0 ? (
                tables.map((table) => (
                  <button
                    type="button"
                    key={table.name}
                    onClick={() => handleTableChange(table.name)}
                    className={`w-full text-left p-3 rounded-lg transition border ${
                      selectedTable === table.name
                        ? 'bg-blue-50 border-blue-500 shadow-sm'
                        : 'bg-gray-50 border-transparent hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <FileJson className={`h-4 w-4 flex-shrink-0 ${selectedTable === table.name ? 'text-blue-600' : 'text-gray-500'}`} />
                      <div className="flex-1 min-w-0">
                        <p className={`font-medium text-sm truncate ${selectedTable === table.name ? 'text-blue-900' : 'text-gray-700'}`}>
                          {table.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {table.row_count?.toLocaleString() || 0}행
                        </p>
                      </div>
                    </div>
                  </button>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500 text-sm">
                  테이블이 없습니다.
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="lg:col-span-3">
        <div className="bg-white rounded-lg shadow min-h-[500px] flex flex-col">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <FileJson className="h-5 w-5 text-blue-600" />
                  {selectedTable || '테이블 선택 필요'}
                </h2>
                <p className="text-sm text-gray-600 mt-1 flex items-center gap-2">
                  <span>총 {totalRows.toLocaleString()}행</span>
                  {totalPages > 0 && (
                    <>
                      <span className="text-gray-300">|</span>
                      <span>페이지 {currentPage} / {totalPages}</span>
                    </>
                  )}
                </p>
              </div>
              <button
                type="button"
                onClick={() => refetchTableData()}
                disabled={isTableFetching || !selectedTable}
                className="flex items-center px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg transition shadow-sm disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isTableFetching ? 'animate-spin' : ''}`} />
                새로고침
              </button>
            </div>
          </div>

          <div className="flex-1 relative">
            {isLoading ? (
              <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
                <div className="flex flex-col items-center">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                  <span className="mt-3 text-gray-600 font-medium">데이터 로딩 중...</span>
                </div>
              </div>
            ) : null}

            {isTableError ? (
              <div className="flex flex-col items-center justify-center h-64 text-red-600">
                <AlertCircle className="h-12 w-12 mb-4" />
                <p>데이터를 불러오는데 실패했습니다.</p>
                <p className="text-sm mt-2 text-red-500">{(tableError as Error).message}</p>
                <button 
                  type="button"
                  onClick={() => refetchTableData()}
                  className="mt-4 px-4 py-2 bg-red-100 hover:bg-red-200 rounded-lg text-sm font-medium transition"
                >
                  다시 시도
                </button>
              </div>
            ) : !selectedTable ? (
              <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                <Table2 className="h-12 w-12 mb-4 text-gray-300" />
                <p>좌측 목록에서 테이블을 선택해주세요.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {columns.length > 0 ? (
                        columns.map((col) => (
                          <th
                            key={col}
                            className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap bg-gray-50 sticky top-0"
                          >
                            {col}
                          </th>
                        ))
                      ) : (
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          정보
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {rows.length > 0 ? (
                      rows.map((row, idx) => (
                        <tr key={String(idx)} className="hover:bg-blue-50/50 transition duration-150">
                          {columns.map((col) => {
                            const { text, fullText } = formatCell(row[col]);
                            return (
                              <td
                                key={`${idx}-${col}`}
                                className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate"
                                title={fullText}
                              >
                                {text}
                              </td>
                            );
                          })}
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td
                          colSpan={columns.length || 1}
                          className="px-4 py-20 text-center text-gray-500"
                        >
                          <div className="flex flex-col items-center justify-center">
                            <FileJson className="h-10 w-10 text-gray-300 mb-3" />
                            <p>표시할 데이터가 없습니다</p>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg flex items-center justify-between sticky bottom-0">
              <div className="text-sm text-gray-600">
                <span className="font-medium">{(currentPage - 1) * PAGE_SIZE + 1}</span>
                {' - '}
                <span className="font-medium">{Math.min(currentPage * PAGE_SIZE, totalRows)}</span>
                {' of '}
                <span className="font-medium">{totalRows.toLocaleString()}</span>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1 || isTableFetching}
                  className="flex items-center px-4 py-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm font-medium text-gray-700"
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  이전
                </button>
                <div className="flex items-center px-2 text-sm font-medium text-gray-700">
                  {currentPage}
                </div>
                <button
                  type="button"
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage >= totalPages || isTableFetching}
                  className="flex items-center px-4 py-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm font-medium text-gray-700"
                >
                  다음
                  <ChevronRight className="h-4 w-4 ml-1" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
