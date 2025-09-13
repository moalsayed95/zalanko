export type SessionUpdateCommand = {
    type: "session.update";
    session: {
        turn_detection?: {
            type: "server_vad" | "none";
        };
        input_audio_transcription?: {
            model: "whisper-1";
        };
    };
};

export type InputAudioBufferAppendCommand = {
    type: "input_audio_buffer.append";
    audio: string;
};

export type InputAudioBufferClearCommand = {
    type: "input_audio_buffer.clear";
};

export type Message = {
    type: string;
};

export type ResponseAudioDelta = {
    type: "response.audio.delta";
    delta: string;
};

export type ResponseAudioTranscriptDelta = {
    type: "response.audio_transcript.delta";
    delta: string;
};

export type ResponseInputAudioTranscriptionCompleted = {
    type: "conversation.item.input_audio_transcription.completed";
    event_id: string;
    item_id: string;
    content_index: number;
    transcript: string;
};

export type ResponseDone = {
    type: "response.done";
    event_id: string;
    response: {
        id: string;
        output: { id: string; content?: { transcript: string; type: string }[] }[];
    };
};

export type ExtensionMiddleTierToolResponse = {
    type: "extension.middle_tier_tool.response";
    previous_item_id: string;
    tool_name: string;
    tool_result: string; // JSON string that needs to be parsed into ToolResult
};

export type Listing = {
    id: string;
    title: string;
    description: string;
    brand: string;
    category: string;
    price: number;
    sale_price?: number;
    on_sale: boolean;
    colors: string[];
    sizes: string[];
    materials: string[];
    style_tags: string[];
    ratings: {
        average?: number;
        count?: number;
    };
    images: string[];
    imageUrls?: string[]; // New field for full Azure Storage URLs
    availability: string;
};

export interface PreferenceFeature {
    id: string;
    label: string;
    icon: string; // Lucide icon name
    enabled: boolean;
}

export interface Preferences {
    budget?: {
        min: number;
        max: number;
    };
    sizes?: {
        tops: string;
        bottoms: string;
        shoes: string;
        dresses: string;
    };
    preferred_brands?: string[];
    style_preferences?: string[];
    preferred_colors?: string[];
    avoided_materials?: string[];
    features: PreferenceFeature[];
}

// Predefined fashion features/preferences
export const AVAILABLE_FEATURES: PreferenceFeature[] = [
    { id: "sustainable", label: "Sustainable Fashion", icon: "Leaf", enabled: false },
    { id: "organic", label: "Organic Materials", icon: "Flower", enabled: false },
    { id: "designer", label: "Designer Brands", icon: "Star", enabled: false },
    { id: "vintage", label: "Vintage Style", icon: "Clock", enabled: false },
    { id: "casual", label: "Casual Wear", icon: "Shirt", enabled: false },
    { id: "formal", label: "Formal Wear", icon: "Tie", enabled: false },
    { id: "sporty", label: "Sportswear", icon: "Dumbbell", enabled: false },
    { id: "sale_only", label: "Sale Items Only", icon: "Percent", enabled: false }
];
