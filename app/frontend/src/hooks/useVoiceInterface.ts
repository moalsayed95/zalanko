import { useState } from "react";
import useRealTime from "@/hooks/useRealtime";
import useAudioRecorder from "@/hooks/useAudioRecorder";
import useAudioPlayer from "@/hooks/useAudioPlayer";

export interface VoiceInterfaceState {
    isRecording: boolean;
    onToggleListening: () => Promise<void>;
}

export interface VoiceInterfaceConfig {
    onToolResponse?: (message: any) => void;
}

/**
 * Custom hook for managing voice interface functionality
 * Handles WebSocket communication, audio recording, and real-time AI interaction
 */
export const useVoiceInterface = (config: VoiceInterfaceConfig = {}): VoiceInterfaceState => {
    const [isRecording, setIsRecording] = useState(false);

    // Setup real-time communication with Azure OpenAI
    const { startSession, addUserAudio, inputAudioBufferClear } = useRealTime({
        onWebSocketOpen: () => {
            console.log("🔌 Voice: WebSocket connection opened");
        },
        onWebSocketClose: () => {
            console.log("🔌 Voice: WebSocket connection closed");
        },
        onWebSocketError: (event) => {
            console.error("🔌 Voice: WebSocket error:", event);
        },
        onReceivedError: (message) => {
            console.error("🔌 Voice: Received error:", message);
        },
        onReceivedResponseAudioDelta: (message) => {
            // Play AI response audio only when recording
            if (isRecording) {
                playAudio(message.delta);
            }
        },
        onReceivedInputAudioBufferSpeechStarted: () => {
            // Stop playing audio when user starts speaking
            stopAudioPlayer();
        },
        onReceivedExtensionMiddleTierToolResponse: (message) => {
            console.log("🛠️ Voice: Tool response received:", message.tool_name);

            // Forward tool responses to parent component if callback provided
            if (config.onToolResponse) {
                config.onToolResponse(message);
            }
        }
    });

    // Setup audio player for AI responses
    const { reset: resetAudioPlayer, play: playAudio, stop: stopAudioPlayer } = useAudioPlayer();

    // Setup audio recorder for user input
    const { start: startAudioRecording, stop: stopAudioRecording } = useAudioRecorder({
        onAudioRecorded: addUserAudio
    });

    /**
     * Toggle voice recording on/off
     * Handles the complete flow of starting/stopping voice interaction
     */
    const onToggleListening = async (): Promise<void> => {
        try {
            if (!isRecording) {
                // Start voice session
                console.log("🎤 Voice: Starting recording session");

                startSession();
                await startAudioRecording();
                resetAudioPlayer();
                setIsRecording(true);

                console.log("✅ Voice: Recording started successfully");
            } else {
                // Stop voice session
                console.log("🛑 Voice: Stopping recording session");

                await stopAudioRecording();
                stopAudioPlayer();
                inputAudioBufferClear();
                setIsRecording(false);

                console.log("✅ Voice: Recording stopped successfully");
            }
        } catch (error) {
            console.error("❌ Voice: Error toggling recording:", error);

            // Reset state on error
            setIsRecording(false);

            // Try to cleanup
            try {
                await stopAudioRecording();
                stopAudioPlayer();
                inputAudioBufferClear();
            } catch (cleanupError) {
                console.error("❌ Voice: Error during cleanup:", cleanupError);
            }
        }
    };

    return {
        isRecording,
        onToggleListening
    };
};

export default useVoiceInterface;