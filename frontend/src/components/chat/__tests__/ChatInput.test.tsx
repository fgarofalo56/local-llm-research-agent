import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@/test/test-utils';
import { ChatInput } from '../ChatInput';

// Mock the chat store
vi.mock('@/stores/chatStore', () => ({
  useChatStore: vi.fn(() => ({
    isStreaming: false,
  })),
}));

import { useChatStore } from '@/stores/chatStore';
const mockUseChatStore = vi.mocked(useChatStore);

describe('ChatInput', () => {
  const mockOnSend = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseChatStore.mockReturnValue({ isStreaming: false });
  });

  it('renders textarea and send button', () => {
    render(<ChatInput onSend={mockOnSend} />);

    expect(screen.getByPlaceholderText(/ask about your data/i)).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('updates textarea value on input', () => {
    render(<ChatInput onSend={mockOnSend} />);

    const textarea = screen.getByPlaceholderText(/ask about your data/i);
    fireEvent.change(textarea, { target: { value: 'Hello world' } });

    expect(textarea).toHaveValue('Hello world');
  });

  it('calls onSend with trimmed content when clicking send button', () => {
    render(<ChatInput onSend={mockOnSend} />);

    const textarea = screen.getByPlaceholderText(/ask about your data/i);
    fireEvent.change(textarea, { target: { value: '  test message  ' } });
    fireEvent.click(screen.getByRole('button'));

    expect(mockOnSend).toHaveBeenCalledWith('test message');
  });

  it('clears input after sending', () => {
    render(<ChatInput onSend={mockOnSend} />);

    const textarea = screen.getByPlaceholderText(/ask about your data/i);
    fireEvent.change(textarea, { target: { value: 'test message' } });
    fireEvent.click(screen.getByRole('button'));

    expect(textarea).toHaveValue('');
  });

  it('sends message on Enter key press', () => {
    render(<ChatInput onSend={mockOnSend} />);

    const textarea = screen.getByPlaceholderText(/ask about your data/i);
    fireEvent.change(textarea, { target: { value: 'test message' } });
    fireEvent.keyDown(textarea, { key: 'Enter' });

    expect(mockOnSend).toHaveBeenCalledWith('test message');
  });

  it('does not send on Shift+Enter (allows multiline)', () => {
    render(<ChatInput onSend={mockOnSend} />);

    const textarea = screen.getByPlaceholderText(/ask about your data/i);
    fireEvent.change(textarea, { target: { value: 'line 1' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('disables button when input is empty', () => {
    render(<ChatInput onSend={mockOnSend} />);

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('disables button when input is only whitespace', () => {
    render(<ChatInput onSend={mockOnSend} />);

    const textarea = screen.getByPlaceholderText(/ask about your data/i);
    fireEvent.change(textarea, { target: { value: '   ' } });

    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('enables button when input has content', () => {
    render(<ChatInput onSend={mockOnSend} />);

    const textarea = screen.getByPlaceholderText(/ask about your data/i);
    fireEvent.change(textarea, { target: { value: 'content' } });

    expect(screen.getByRole('button')).not.toBeDisabled();
  });

  it('does not send empty message', () => {
    render(<ChatInput onSend={mockOnSend} />);

    const textarea = screen.getByPlaceholderText(/ask about your data/i);
    fireEvent.keyDown(textarea, { key: 'Enter' });

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  describe('when streaming', () => {
    beforeEach(() => {
      mockUseChatStore.mockReturnValue({ isStreaming: true });
    });

    it('disables textarea when streaming', () => {
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(/ask about your data/i);
      expect(textarea).toBeDisabled();
    });

    it('disables send button when streaming', () => {
      render(<ChatInput onSend={mockOnSend} />);

      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('does not send message when streaming', () => {
      render(<ChatInput onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(/ask about your data/i);
      fireEvent.change(textarea, { target: { value: 'test' } });
      fireEvent.keyDown(textarea, { key: 'Enter' });

      expect(mockOnSend).not.toHaveBeenCalled();
    });
  });
});
