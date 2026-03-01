interface WelcomeScreenProps {
  onLogin: () => void;
  onRegister: () => void;
}

export function WelcomeScreen({ onLogin, onRegister }: WelcomeScreenProps) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="dark-header py-2 px-6">
        <h1 className="text-center text-lg">KI Tutor</h1>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center py-4">
        <div className="w-96">
          <div className="ki-card p-4">
            <div className="text-center mb-3">
              <h2 className="ki-title mb-2 text-lg">Willkommen bei KI Tutor</h2>
            </div>

            <div className="flex flex-col items-center gap-2">
              <button
                onClick={onLogin}
                className="ki-button-primary w-full px-8 py-2 text-sm"
              >
                Anmelden
              </button>
              
              <button
                onClick={onRegister}
                className="ki-link text-xs"
              >
                Registrieren
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
