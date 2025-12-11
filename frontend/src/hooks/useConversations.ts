import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import type { Conversation, Message } from '@/types';

interface ConversationsResponse {
  conversations: Conversation[];
  total: number;
}

interface MessagesResponse {
  messages: Message[];
  total: number;
}

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: () => api.get<ConversationsResponse>('/conversations'),
  });
}

export function useConversation(id: number | null) {
  return useQuery({
    queryKey: ['conversation', id],
    queryFn: () => api.get<Conversation>(`/conversations/${id}`),
    enabled: id !== null,
  });
}

export function useMessages(conversationId: number | null) {
  return useQuery({
    queryKey: ['messages', conversationId],
    queryFn: () => api.get<MessagesResponse>(`/conversations/${conversationId}/messages`),
    enabled: conversationId !== null,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (title: string | undefined = undefined) =>
      api.post<Conversation>('/conversations', title ? { title } : {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/conversations/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}
