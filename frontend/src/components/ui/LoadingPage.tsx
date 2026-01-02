export function LoadingPage() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600"></div>
        <p className="text-sm text-gray-500">Loading...</p>
      </div>
    </div>
  );
}
