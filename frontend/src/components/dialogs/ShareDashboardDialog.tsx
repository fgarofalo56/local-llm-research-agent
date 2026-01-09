// frontend/src/components/dialogs/ShareDashboardDialog.tsx
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Copy, Check, Link, Trash2 } from 'lucide-react';
import { api } from '@/api/client';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface ShareDashboardDialogProps {
  open: boolean;
  onClose: () => void;
  dashboardId: number;
  existingShareUrl?: string;
  expiresAt?: string;
}

export function ShareDashboardDialog({
  open,
  onClose,
  dashboardId,
  existingShareUrl,
  expiresAt,
}: ShareDashboardDialogProps) {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);
  const [expiresInDays, setExpiresInDays] = useState(7);

  const createShareMutation = useMutation({
    mutationFn: () =>
      api.post<{ share_url: string; expires_at: string }>(
        `/dashboards/${dashboardId}/share`,
        { expires_in_days: expiresInDays }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
    },
  });

  const revokeShareMutation = useMutation({
    mutationFn: () => api.delete(`/dashboards/${dashboardId}/share`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
    },
  });

  const shareUrl = existingShareUrl
    ? `${window.location.origin}${existingShareUrl}`
    : createShareMutation.data?.share_url
      ? `${window.location.origin}${createShareMutation.data.share_url}`
      : null;

  const handleCopy = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-lg">
          <Dialog.Title className="flex items-center gap-2 text-lg font-semibold">
            <Link className="h-5 w-5" />
            Share Dashboard
          </Dialog.Title>

          <div className="mt-4 space-y-4">
            {shareUrl ? (
              <>
                <div>
                  <label className="mb-1 block text-sm font-medium">
                    Share Link
                  </label>
                  <div className="flex gap-2">
                    <Input value={shareUrl} readOnly className="flex-1" />
                    <Button variant="outline" size="icon" onClick={handleCopy}>
                      {copied ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                {(expiresAt || createShareMutation.data?.expires_at) && (
                  <p className="text-sm text-muted-foreground">
                    Expires:{' '}
                    {new Date(
                      expiresAt || createShareMutation.data!.expires_at
                    ).toLocaleDateString()}
                  </p>
                )}

                <Button
                  variant="destructive"
                  onClick={() => revokeShareMutation.mutate()}
                  disabled={revokeShareMutation.isPending}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Revoke Link
                </Button>
              </>
            ) : (
              <>
                <div>
                  <label className="mb-1 block text-sm font-medium">
                    Link expires in
                  </label>
                  <select
                    value={expiresInDays}
                    onChange={(e) => setExpiresInDays(parseInt(e.target.value))}
                    className="w-full rounded-md border bg-background px-3 py-2"
                  >
                    <option value={1}>1 day</option>
                    <option value={7}>7 days</option>
                    <option value={30}>30 days</option>
                    <option value={90}>90 days</option>
                  </select>
                </div>

                <div className="rounded-md bg-muted p-3">
                  <p className="text-sm text-muted-foreground">
                    Anyone with this link will be able to view this dashboard
                    without logging in.
                  </p>
                </div>

                <Button
                  onClick={() => createShareMutation.mutate()}
                  disabled={createShareMutation.isPending}
                  className="w-full"
                >
                  Create Share Link
                </Button>
              </>
            )}
          </div>

          <Dialog.Close asChild>
            <button
              className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
