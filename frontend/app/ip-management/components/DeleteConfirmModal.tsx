'use client';

import { IPRecord } from './types';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  record: IPRecord | null;
  onConfirm: () => void;
  onClose: () => void;
}

export function DeleteConfirmModal({
  isOpen,
  record,
  onConfirm,
  onClose,
}: DeleteConfirmModalProps) {
  if (!isOpen || !record) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
      onKeyDown={(e) => e.key === 'Escape' && onClose()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-modal-title"
        className="bg-white rounded-lg p-6 w-full max-w-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="delete-modal-title" className="text-xl font-bold mb-4 text-gray-900">
          삭제 확인
        </h2>
        <p className="text-gray-600 mb-6">
          정말로 <span className="font-mono font-semibold">{record.ip_address}</span>를
          삭제하시겠습니까?
        </p>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onConfirm}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
          >
            삭제
          </button>
          <button
            type="button"
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition"
          >
            취소
          </button>
        </div>
      </div>
    </div>
  );
}
