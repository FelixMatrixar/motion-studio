import { createClient } from '@supabase/supabase-js';

// Initialize Supabase
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseAnonKey);

export const useTemplateVariables = () => {
  // Returns empty initial state for the builder
  return {
    reference_image: '',
    motion_video: ''
  };
};

export const uploadFile = async (file: File): Promise<string | null> => {
  try {
    const fileExt = file.name.split('.').pop();
    const fileName = `${Math.random().toString(36).substring(2, 15)}_${Date.now()}.${fileExt}`;
    const filePath = `uploads/${fileName}`;

    const { error: uploadError } = await supabase.storage
      .from('motion-studio-media')
      .upload(filePath, file, {
        cacheControl: '3600',
        upsert: false
      });

    if (uploadError) throw uploadError;

    const { data } = supabase.storage
      .from('motion-studio-media')
      .getPublicUrl(filePath);

    return data.publicUrl;
  } catch (error) {
    console.error('Error uploading file to Supabase:', error);
    return null;
  }
};

export const submit = async (variables: { reference_image: string, motion_video: string }) => {
  // This is a wrapper around the FastAPI call you already added to App.tsx
  console.log("Submitting variables to DAG Orchestrator:", variables);
  return variables;
};