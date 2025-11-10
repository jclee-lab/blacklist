'use client';

import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, CheckCircle, XCircle, Search, Filter } from 'lucide-react';

interface IPRecord {
  id: number;
  ip_address: string;
  reason: string;
  source: string;
  country?: string;
  detection_count?: number;
  is_active?: boolean;
  detection_date?: string;
  removal_date?: string;
  created_at: string;
  updated_at: string;
  list_type?: string;
}

export default function IPManagementClient() {
  const [activeTab, setActiveTab] = useState<'unified' | 'whitelist' | 'blacklist'>('unified');
  const [data, setData] = useState<IPRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingRecord, setEditingRecord] = useState<IPRecord | null>(null);

  // Form states
  const [formData, setFormData] = useState({
    ip_address: '',
    reason: '',
    source: 'MANUAL',
    country: '',
    is_active: true,
    detection_date: '',
    removal_date: '',
  });

  // Filters
  const [filterType, setFilterType] = useState<string>('');
  const [searchIP, setSearchIP] = useState('');

  useEffect(() => {
    fetchData();
  }, [activeTab, page, filterType]);

  const fetchData = async () => {
    setLoading(true);
    try {
      let url = '';
      const params = new URLSearchParams({ page: page.toString(), limit: '20' });

      if (activeTab === 'unified') {
        if (filterType) params.append('type', filterType);
        if (searchIP) params.append('ip', searchIP);
        url = `/api/ip/unified?${params}`;
      } else if (activeTab === 'whitelist') {
        url = `/api/ip/whitelist?${params}`;
      } else {
        url = `/api/ip/blacklist?${params}`;
      }

      const res = await fetch(url);
      const json = await res.json();

      if (json.success) {
        setData(json.data || []);
        setTotal(json.total || 0);
        setTotalPages(json.total_pages || 0);
      }
    } catch (error) {
      console.error('Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    try {
      const listType = activeTab === 'whitelist' || activeTab === 'unified' ? 'whitelist' : 'blacklist';
      const endpoint = `/api/ip/${listType}`;

      const body: any = {
        ip_address: formData.ip_address,
        reason: formData.reason,
        source: formData.source,
        country: formData.country || null,
      };

      if (listType === 'blacklist') {
        body.is_active = formData.is_active;
        if (formData.detection_date) body.detection_date = formData.detection_date;
        if (formData.removal_date) body.removal_date = formData.removal_date;
      }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const json = await res.json();

      if (json.success) {
        alert(json.message || '추가되었습니다.');
        setShowAddModal(false);
        resetForm();
        fetchData();
      } else {
        alert(`오류: ${json.error}`);
      }
    } catch (error) {
      alert(`추가 실패: ${error}`);
    }
  };

  const handleEdit = async () => {
    if (!editingRecord) return;

    try {
      const listType = editingRecord.list_type === 'whitelist' ? 'whitelist' : 'blacklist';
      const endpoint = `/api/ip/${listType}/${editingRecord.id}`;

      const body: any = {
        ip_address: formData.ip_address,
        reason: formData.reason,
        source: formData.source,
        country: formData.country || null,
      };

      if (listType === 'blacklist') {
        body.is_active = formData.is_active;
        if (formData.detection_date) body.detection_date = formData.detection_date;
        if (formData.removal_date) body.removal_date = formData.removal_date;
      }

      const res = await fetch(endpoint, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const json = await res.json();

      if (json.success) {
        alert(json.message || '수정되었습니다.');
        setShowEditModal(false);
        setEditingRecord(null);
        resetForm();
        fetchData();
      } else {
        alert(`오류: ${json.error}`);
      }
    } catch (error) {
      alert(`수정 실패: ${error}`);
    }
  };

  const handleDelete = async (record: IPRecord) => {
    if (!confirm(`정말로 ${record.ip_address}를 삭제하시겠습니까?`)) return;

    try {
      const listType = record.list_type === 'whitelist' || activeTab === 'whitelist' ? 'whitelist' : 'blacklist';
      const endpoint = `/api/ip/${listType}/${record.id}`;

      const res = await fetch(endpoint, { method: 'DELETE' });
      const json = await res.json();

      if (json.success) {
        alert(json.message || '삭제되었습니다.');
        fetchData();
      } else {
        alert(`오류: ${json.error}`);
      }
    } catch (error) {
      alert(`삭제 실패: ${error}`);
    }
  };

  const openEditModal = (record: IPRecord) => {
    setEditingRecord(record);
    setFormData({
      ip_address: record.ip_address,
      reason: record.reason,
      source: record.source,
      country: record.country || '',
      is_active: record.is_active !== undefined ? record.is_active : true,
      detection_date: record.detection_date || '',
      removal_date: record.removal_date || '',
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      ip_address: '',
      reason: '',
      source: 'MANUAL',
      country: '',
      is_active: true,
      detection_date: '',
      removal_date: '',
    });
  };

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200">
        <button
          onClick={() => { setActiveTab('unified'); setPage(1); }}
          className={`px-6 py-3 font-medium border-b-2 transition ${
            activeTab === 'unified'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          통합 뷰
        </button>
        <button
          onClick={() => { setActiveTab('whitelist'); setPage(1); }}
          className={`px-6 py-3 font-medium border-b-2 transition ${
            activeTab === 'whitelist'
              ? 'border-green-500 text-green-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          화이트리스트
        </button>
        <button
          onClick={() => { setActiveTab('blacklist'); setPage(1); }}
          className={`px-6 py-3 font-medium border-b-2 transition ${
            activeTab === 'blacklist'
              ? 'border-red-500 text-red-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          블랙리스트
        </button>
      </div>

      {/* Filters & Actions */}
      <div className="flex flex-wrap items-center gap-4">
        {activeTab === 'unified' && (
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="">전체</option>
            <option value="whitelist">화이트리스트만</option>
            <option value="blacklist">블랙리스트만</option>
          </select>
        )}

        <div className="flex items-center gap-2 flex-1 max-w-md">
          <input
            type="text"
            placeholder="IP 주소 검색..."
            value={searchIP}
            onChange={(e) => setSearchIP(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && fetchData()}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
          />
          <button
            onClick={() => fetchData()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
          >
            <Search className="h-5 w-5" />
          </button>
          {searchIP && (
            <button
              onClick={() => {
                setSearchIP('');
                setPage(1);
                // searchIP를 빈 값으로 강제 설정하여 즉시 fetchData 호출
                setTimeout(() => fetchData(), 0);
              }}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
            >
              초기화
            </button>
          )}
        </div>

        {activeTab !== 'unified' && (
          <button
            onClick={() => { setShowAddModal(true); resetForm(); }}
            className="ml-auto px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-2"
          >
            <Plus className="h-5 w-5" />
            추가
          </button>
        )}
      </div>

      {/* Data Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">로딩 중...</div>
        ) : data.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {activeTab === 'unified' && (
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        구분
                      </th>
                    )}
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">사유</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">소스</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">국가</th>
                    {(activeTab === 'blacklist' || activeTab === 'unified') && (
                      <>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">상태</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">탐지일</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">해제일</th>
                      </>
                    )}
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">등록일</th>
                    {activeTab !== 'unified' && (
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">작업</th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-50">
                      {activeTab === 'unified' && (
                        <td className="px-4 py-3 text-sm">
                          {record.list_type === 'whitelist' ? (
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                              화이트
                            </span>
                          ) : (
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                              블랙
                            </span>
                          )}
                        </td>
                      )}
                      <td className="px-4 py-3 text-sm font-mono">{record.ip_address}</td>
                      <td className="px-4 py-3 text-sm max-w-xs" title={record.reason}>
                        <div className="whitespace-normal break-words">{record.reason}</div>
                      </td>
                      <td className="px-4 py-3 text-sm">{record.source}</td>
                      <td className="px-4 py-3 text-sm">{record.country || '-'}</td>
                      {(activeTab === 'blacklist' || activeTab === 'unified') && (
                        <>
                          <td className="px-4 py-3 text-sm">
                            {record.is_active !== undefined && (
                              record.is_active ? (
                                <CheckCircle className="h-5 w-5 text-green-500 inline" />
                              ) : (
                                <XCircle className="h-5 w-5 text-gray-400 inline" />
                              )
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm whitespace-nowrap">
                            {record.detection_date ? new Date(record.detection_date).toLocaleDateString('ko-KR') : '-'}
                          </td>
                          <td className="px-4 py-3 text-sm whitespace-nowrap">
                            {record.removal_date ? new Date(record.removal_date).toLocaleDateString('ko-KR') : '-'}
                          </td>
                        </>
                      )}
                      <td className="px-4 py-3 text-sm whitespace-nowrap">
                        {record.created_at ? new Date(record.created_at).toLocaleDateString('ko-KR') : '-'}
                      </td>
                      {activeTab !== 'unified' && (
                        <td className="px-4 py-3 text-sm">
                          <div className="flex gap-2">
                            <button
                              onClick={() => openEditModal(record)}
                              className="text-blue-600 hover:text-blue-800"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(record)}
                              className="text-red-600 hover:text-red-800"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  총 {total}개 (페이지 {page}/{totalPages})
                </div>
                <div className="flex gap-2">
                  {page > 1 && (
                    <button
                      onClick={() => setPage(page - 1)}
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      이전
                    </button>
                  )}
                  {page < totalPages && (
                    <button
                      onClick={() => setPage(page + 1)}
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      다음
                    </button>
                  )}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="p-8 text-center text-gray-500">데이터가 없습니다</div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">
              {activeTab === 'whitelist' ? '화이트리스트' : '블랙리스트'} 추가
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">IP 주소 *</label>
                <input
                  type="text"
                  value={formData.ip_address}
                  onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
                  placeholder="192.168.1.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  사유 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.reason}
                  onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                  placeholder={activeTab === 'whitelist' ? 'VIP 고객' : '악성 활동'}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">소스</label>
                <select
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="MANUAL">수동 입력</option>
                  <option value="REGTECH">REGTECH</option>
                  <option value="AUTO">자동</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">국가 코드</label>
                <input
                  type="text"
                  value={formData.country}
                  onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                  placeholder="KR"
                  maxLength={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              {activeTab === 'blacklist' && (
                <>
                  <div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.is_active}
                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                        className="rounded"
                      />
                      <span className="text-sm font-medium text-gray-700">활성화</span>
                    </label>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      탐지일 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      value={formData.detection_date}
                      onChange={(e) => {
                        const detectionDate = e.target.value;
                        setFormData({ ...formData, detection_date: detectionDate });

                        // 탐지일 + 3개월 = 해제일 자동 계산
                        if (detectionDate) {
                          const date = new Date(detectionDate);
                          date.setMonth(date.getMonth() + 3);
                          const removalDate = date.toISOString().split('T')[0];
                          setFormData((prev) => ({ ...prev, detection_date: detectionDate, removal_date: removalDate }));
                        }
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      해제일 (자동: 탐지일 + 3개월) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      value={formData.removal_date}
                      onChange={(e) => setFormData({ ...formData, removal_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      placeholder="탐지일 입력 시 자동 계산됩니다"
                      required
                    />
                  </div>
                </>
              )}
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleAdd}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                추가
              </button>
              <button
                onClick={() => { setShowAddModal(false); resetForm(); }}
                className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editingRecord && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">
              {editingRecord.list_type === 'whitelist' || activeTab === 'whitelist' ? '화이트리스트' : '블랙리스트'} 수정
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">IP 주소 *</label>
                <input
                  type="text"
                  value={formData.ip_address}
                  onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">사유 *</label>
                <input
                  type="text"
                  value={formData.reason}
                  onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">소스</label>
                <select
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="MANUAL">수동 입력</option>
                  <option value="REGTECH">REGTECH</option>
                  <option value="AUTO">자동</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">국가 코드</label>
                <input
                  type="text"
                  value={formData.country}
                  onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                  maxLength={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              {(editingRecord.list_type === 'blacklist' || activeTab === 'blacklist') && (
                <>
                  <div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.is_active}
                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                        className="rounded"
                      />
                      <span className="text-sm font-medium text-gray-700">활성화</span>
                    </label>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      탐지일 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      value={formData.detection_date}
                      onChange={(e) => {
                        const detectionDate = e.target.value;
                        setFormData({ ...formData, detection_date: detectionDate });

                        // 탐지일 + 3개월 = 해제일 자동 계산
                        if (detectionDate) {
                          const date = new Date(detectionDate);
                          date.setMonth(date.getMonth() + 3);
                          const removalDate = date.toISOString().split('T')[0];
                          setFormData((prev) => ({ ...prev, detection_date: detectionDate, removal_date: removalDate }));
                        }
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      해제일 (자동: 탐지일 + 3개월) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      value={formData.removal_date}
                      onChange={(e) => setFormData({ ...formData, removal_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      placeholder="탐지일 입력 시 자동 계산됩니다"
                      required
                    />
                  </div>
                </>
              )}
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleEdit}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                수정
              </button>
              <button
                onClick={() => { setShowEditModal(false); setEditingRecord(null); resetForm(); }}
                className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
