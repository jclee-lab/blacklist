'use client';

import { useState, useEffect } from 'react';
import { Table2, FileJson, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react';

interface TableSchema {
  name: string;
  row_count: number;
}

export default function TableBrowserClient() {
  const [tables, setTables] = useState<TableSchema[]>([]);
  const [selectedTable, setSelectedTable] = useState('blacklist_ips');
  const [tableData, setTableData] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSchema();
  }, []);

  useEffect(() => {
    fetchTableData();
  }, [selectedTable, currentPage]);

  const fetchSchema = async () => {
    try {
      const res = await fetch('/api/database/schema');
      if (res.ok) {
        const data = await res.json();
        setTables(data?.tables || []);
      }
    } catch (error) {
      console.error('Failed to fetch schema:', error);
    }
  };

  const fetchTableData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/database/table/${selectedTable}?page=${currentPage}&limit=50`);
      if (res.ok) {
        const data = await res.json();
        setTableData(data);
      }
    } catch (error) {
      console.error('Failed to fetch table data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (tableName: string) => {
    setSelectedTable(tableName);
    setCurrentPage(1);
  };

  const data = tableData?.data || [];
  const columns = tableData?.columns || [];
  const totalRows = tableData?.total || 0;
  const totalPages = Math.ceil(totalRows / 50);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Sidebar - Table List */}
      <div className="lg:col-span-1">
        <div className="bg-white rounded-lg shadow p-4 sticky top-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Table2 className="h-5 w-5" />
            테이블 목록
          </h2>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {tables.map((table) => (
              <button
                key={table.name}
                onClick={() => handleTableChange(table.name)}
                className={`w-full text-left p-3 rounded-lg transition ${
                  selectedTable === table.name
                    ? 'bg-blue-50 border-2 border-blue-500'
                    : 'bg-gray-50 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-center gap-2">
                  <FileJson className="h-4 w-4 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{table.name}</p>
                    <p className="text-xs text-gray-500">
                      {table.row_count?.toLocaleString() || 0}행
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content - Table Data */}
      <div className="lg:col-span-3">
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <FileJson className="h-5 w-5" />
                  {selectedTable}
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  총 {totalRows.toLocaleString()}행 {totalPages > 0 && `(페이지 ${currentPage}/${totalPages})`}
                </p>
              </div>
              <button
                onClick={fetchTableData}
                className="flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                새로고침
              </button>
            </div>
          </div>

          {/* Table Data */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
              <span className="ml-3 text-gray-600">데이터 로딩 중...</span>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {columns.map((col: string) => (
                      <th
                        key={col}
                        className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.length > 0 ? (
                    data.map((row: any, idx: number) => (
                      <tr key={idx} className="hover:bg-gray-50 transition">
                        {columns.map((col: string) => (
                          <td
                            key={col}
                            className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate"
                            title={typeof row[col] === 'object' ? JSON.stringify(row[col]) : String(row[col] || '-')}
                          >
                            {typeof row[col] === 'object'
                              ? JSON.stringify(row[col]).substring(0, 100)
                              : String(row[col] || '-')}
                          </td>
                        ))}
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={columns.length || 1}
                        className="px-4 py-12 text-center text-gray-500"
                      >
                        데이터가 없습니다
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                {(currentPage - 1) * 50 + 1}-{Math.min(currentPage * 50, totalRows)} of{' '}
                {totalRows.toLocaleString()}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  이전
                </button>
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage >= totalPages}
                  className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
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
