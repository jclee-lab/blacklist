'use client';

import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { CredentialFormState } from './types';

interface CredentialEditModalProps {
  show: boolean;
  onClose: () => void;
  editingService: string | null;
  credentialForm: CredentialFormState;
  onFormChange: (form: CredentialFormState) => void;
  onSave: () => void;
  loading?: boolean;
}

export function CredentialEditModal({
  show,
  onClose,
  editingService,
  credentialForm,
  onFormChange,
  onSave,
  loading = false,
}: CredentialEditModalProps) {
  return (
    <Modal isOpen={show} onClose={onClose} title={`${editingService} 인증정보 수정`} size="md">
      <div className="space-y-4">
        <Input
          label="사용자명"
          value={credentialForm.username}
          onChange={(e) => onFormChange({ ...credentialForm, username: e.target.value })}
          placeholder="사용자명"
        />
        <Input
          label="비밀번호"
          type="password"
          value={credentialForm.password}
          onChange={(e) => onFormChange({ ...credentialForm, password: e.target.value })}
          placeholder="변경하지 않으려면 비워두세요"
        />
        <Input
          label="수집 주기 (초)"
          type="number"
          value={credentialForm.collection_interval}
          onChange={(e) =>
            onFormChange({
              ...credentialForm,
              collection_interval: e.target.value,
            })
          }
          placeholder="3600"
        />
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="enabled"
            checked={credentialForm.enabled}
            onChange={(e) => onFormChange({ ...credentialForm, enabled: e.target.checked })}
            className="h-4 w-4 rounded border-gray-300"
          />
          <label htmlFor="enabled" className="text-sm text-gray-700">
            활성화
          </label>
        </div>
        <div className="flex justify-end space-x-2 pt-4">
          <Button variant="secondary" onClick={onClose}>
            취소
          </Button>
          <Button onClick={onSave} loading={loading}>
            저장
          </Button>
        </div>
      </div>
    </Modal>
  );
}
