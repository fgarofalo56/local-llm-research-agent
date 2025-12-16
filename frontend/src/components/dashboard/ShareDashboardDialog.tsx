/**
 * Share Dashboard Dialog
 * Phase 2.5: Advanced Features & Polish
 *
 * Dialog for creating and managing dashboard share links.
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Copy, Check, Link, Trash2, Clock, Globe } from 'lucide-react';
import { api } from '../../api/client';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';

interface ShareDashboardDialogProps {
  dashboardId: number;
  dashboardName: string;
  existingShareToken?: string | null;
  existingExpiresAt?: string | null;
  onClose: () => void;
}

interface ShareLinkResponse {
  share_token: string;
  share_url: string;
  expires_at: string | null;
  is_public: boolean;
}

export function ShareDashboardDialog({
  dashboardId,
  dashboardName,
  existingShareToken,
  existingExpiresAt,
  onClose,
}: ShareDashboardDialogProps) {
  const [expiresHours, setExpiresHours] = useState<number>(24);
  const [copied, setCopied] = useState(false);
  const queryClient = useQueryClient();

  const createShareMutation = useMutation({
    mutationFn: async () => {
      return api.post<ShareLinkResponse>(`/dashboards/${dashboardId}/share`, {
        expires_hours: expiresHours,
        is_public: true,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', dashboardId] });
    },
  });

  const revokeShareMutation = useMutation({
    mutationFn: async () => {
      return api.delete(`/dashboards/${dashboardId}/share`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', dashboardId] });
    },
  });

  const shareToken = createShareMutation.data?.share_token || existingShareToken;
  const expiresAt = createShareMutation.data?.expires_at || existingExpiresAt;

  const shareUrl = shareToken
    ? `${window.location.origin}/shared/${shareToken}`
    : null;

  const handleCopy = async () => {
    if (shareUrl) {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleCreateShare = () => {
    createShareMutation.mutate();
  };

  const handleRevokeShare = () => {
    if (confirm('Are you sure you want to revoke the share link? Anyone with the link will no longer be able to access the dashboard.')) {
      revokeShareMutation.mutate();
    }
  };

  const formatExpiry = (expiresAt: string | null) => {
    if (!expiresAt) return 'Never expires';
    const date = new Date(expiresAt);
    const now = new Date();
    if (date < now) return 'Expired';
    return `Expires ${date.toLocaleDateString()} at ${date.toLocaleTimeString()}`;
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md mx-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Share Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Create a public link to share "{dashboardName}" with others.
          </p>

          {shareToken ? (
            // Share link exists
            <div className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={shareUrl || ''}
                  readOnly
                  className="flex-1 font-mono text-sm"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleCopy}
                  title="Copy link"
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>

              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                {formatExpiry(expiresAt || null)}
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={handleRevokeShare}
                  disabled={revokeShareMutation.isPending}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Revoke Link
                </Button>
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={handleCreateShare}
                  disabled={createShareMutation.isPending}
                >
                  <Link className="h-4 w-4 mr-2" />
                  New Link
                </Button>
              </div>
            </div>
          ) : (
            // No share link yet
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-1 block">
                  Link expiration
                </label>
                <select
                  value={expiresHours}
                  onChange={(e) => setExpiresHours(parseInt(e.target.value))}
                  className="w-full px-3 py-2 rounded-md border border-input bg-background"
                >
                  <option value={1}>1 hour</option>
                  <option value={24}>24 hours</option>
                  <option value={168}>7 days</option>
                  <option value={720}>30 days</option>
                  <option value={0}>Never expires</option>
                </select>
              </div>

              <Button
                className="w-full"
                onClick={handleCreateShare}
                disabled={createShareMutation.isPending}
              >
                <Link className="h-4 w-4 mr-2" />
                {createShareMutation.isPending ? 'Creating...' : 'Create Share Link'}
              </Button>
            </div>
          )}

          {(createShareMutation.isError || revokeShareMutation.isError) && (
            <p className="text-sm text-destructive">
              An error occurred. Please try again.
            </p>
          )}

          <div className="flex justify-end pt-2">
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ShareDashboardDialog;
