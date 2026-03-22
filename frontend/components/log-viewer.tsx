interface LogViewerProps {
  logs: string[]
}

export function LogViewer({ logs }: LogViewerProps) {
  return (
    <div className="bg-background/50 rounded-lg border border-border p-4 font-mono text-sm h-64 overflow-y-auto">
      {logs.length === 0 ? (
        <div className="text-muted-foreground text-center py-8">
          <p>Logs will appear here when generation starts</p>
        </div>
      ) : (
        <div className="space-y-1">
          {logs.map((log, idx) => (
            <div key={idx} className="text-muted-foreground">
              <span className="text-primary">{log}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
