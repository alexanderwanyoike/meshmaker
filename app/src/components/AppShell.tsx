import { useState } from 'react';
import { Wizard } from './wizard/Wizard';
import { MeshTool } from './tools/MeshTool';
import { RigTool } from './tools/RigTool';
import { AnimateTool } from './tools/AnimateTool';
import { Settings } from './Settings';

type AppMode = 'pipeline' | 'mesh' | 'rig' | 'animate';

interface SidebarEntry {
  id: AppMode;
  label: string;
  description: string;
}

const entries: SidebarEntry[] = [
  { id: 'pipeline', label: 'Full Pipeline', description: 'Image to rigged + animated FBX' },
  { id: 'mesh', label: 'Mesh Generator', description: 'Image to GLB' },
  { id: 'rig', label: 'Auto Rigger', description: 'GLB to rigged FBX' },
  { id: 'animate', label: 'Animator', description: 'FBX + prompt to animated FBX' },
];

export function AppShell() {
  const [mode, setMode] = useState<AppMode>('pipeline');
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900 overflow-hidden">
      <aside className="w-44 flex flex-col bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 shrink-0">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h1 className="text-lg font-bold text-gray-900 dark:text-white">CharMaker</h1>
        </div>
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {entries.map((entry) => (
            <button
              key={entry.id}
              onClick={() => setMode(entry.id)}
              className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                mode === entry.id
                  ? 'bg-blue-500 text-white rounded-lg'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <div className="text-sm font-medium leading-tight">{entry.label}</div>
              <div
                className={`text-xs mt-0.5 leading-tight ${
                  mode === entry.id ? 'text-blue-100' : 'text-gray-400 dark:text-gray-500'
                }`}
              >
                {entry.description}
              </div>
            </button>
          ))}
        </nav>
        <div className="p-2 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setShowSettings(true)}
            className="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            Settings
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        {mode === 'pipeline' && <Wizard hideHeader />}
        {mode === 'mesh' && <MeshTool />}
        {mode === 'rig' && <RigTool />}
        {mode === 'animate' && <AnimateTool />}
      </main>
      {showSettings && <Settings onClose={() => setShowSettings(false)} />}
    </div>
  );
}
