import { open, save } from '@tauri-apps/plugin-dialog';

export function useFilePicker() {
  const pickImage = async (): Promise<string | null> => {
    const result = await open({
      multiple: false,
      filters: [
        {
          name: 'Image',
          extensions: ['png', 'jpg', 'jpeg', 'webp'],
        },
      ],
    });
    return result as string | null;
  };

  const pickSaveLocation = async (defaultName: string): Promise<string | null> => {
    const result = await save({
      defaultPath: defaultName,
      filters: [
        {
          name: '3D Model',
          extensions: ['fbx', 'glb'],
        },
      ],
    });
    return result;
  };

  return { pickImage, pickSaveLocation };
}
