'use client';

import { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Download, Maximize2, SkipBack, SkipForward } from 'lucide-react';

interface CallRecordingPlayerProps {
    recordingUrl: string;
    callId: string;
    callDate: string;
    duration: number; // in seconds
    participantName?: string;
    onDownload?: () => void;
}

export default function CallRecordingPlayer({
    recordingUrl,
    callId,
    callDate,
    duration,
    participantName,
    onDownload,
}: CallRecordingPlayerProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [isMuted, setIsMuted] = useState(false);
    const [volume, setVolume] = useState(1);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        const video = videoRef.current;
        if (!video) return;

        const handleTimeUpdate = () => setCurrentTime(video.currentTime);
        const handleEnded = () => setIsPlaying(false);
        const handleLoadedData = () => setLoading(false);
        const handleError = () => { setError(true); setLoading(false); };

        video.addEventListener('timeupdate', handleTimeUpdate);
        video.addEventListener('ended', handleEnded);
        video.addEventListener('loadeddata', handleLoadedData);
        video.addEventListener('error', handleError);

        return () => {
            video.removeEventListener('timeupdate', handleTimeUpdate);
            video.removeEventListener('ended', handleEnded);
            video.removeEventListener('loadeddata', handleLoadedData);
            video.removeEventListener('error', handleError);
        };
    }, []);

    const togglePlay = () => {
        if (!videoRef.current) return;
        if (isPlaying) {
            videoRef.current.pause();
        } else {
            videoRef.current.play();
        }
        setIsPlaying(!isPlaying);
    };

    const toggleMute = () => {
        if (!videoRef.current) return;
        videoRef.current.muted = !isMuted;
        setIsMuted(!isMuted);
    };

    const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!videoRef.current) return;
        const newVolume = parseFloat(e.target.value);
        videoRef.current.volume = newVolume;
        setVolume(newVolume);
        setIsMuted(newVolume === 0);
    };

    const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!videoRef.current) return;
        const time = parseFloat(e.target.value);
        videoRef.current.currentTime = time;
        setCurrentTime(time);
    };

    const skip = (seconds: number) => {
        if (!videoRef.current) return;
        videoRef.current.currentTime = Math.min(
            Math.max(0, videoRef.current.currentTime + seconds),
            duration
        );
    };

    const toggleFullscreen = () => {
        if (!videoRef.current) return;
        if (!isFullscreen) {
            videoRef.current.requestFullscreen?.();
        } else {
            document.exitFullscreen?.();
        }
        setIsFullscreen(!isFullscreen);
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    if (error) {
        return (
            <div className="bg-gray-900 rounded-xl p-8 text-center">
                <div className="text-gray-400 mb-4">
                    <Volume2 className="w-12 h-12 mx-auto opacity-50" />
                </div>
                <p className="text-white mb-2">Recording Unavailable</p>
                <p className="text-gray-400 text-sm">
                    This recording may have expired or been deleted.
                </p>
            </div>
        );
    }

    return (
        <div className="bg-gray-900 rounded-xl overflow-hidden">
            {/* Video */}
            <div className="relative aspect-video bg-black">
                {loading && (
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                )}
                <video
                    ref={videoRef}
                    src={recordingUrl}
                    className="w-full h-full"
                    playsInline
                />

                {/* Play Overlay */}
                {!isPlaying && !loading && (
                    <button
                        onClick={togglePlay}
                        className="absolute inset-0 flex items-center justify-center bg-black/30 hover:bg-black/40 transition-colors"
                    >
                        <div className="w-16 h-16 bg-white/90 rounded-full flex items-center justify-center">
                            <Play className="w-8 h-8 text-gray-900 ml-1" />
                        </div>
                    </button>
                )}
            </div>

            {/* Controls */}
            <div className="p-4 space-y-3">
                {/* Progress */}
                <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 w-10">{formatTime(currentTime)}</span>
                    <input
                        type="range"
                        min={0}
                        max={duration}
                        value={currentTime}
                        onChange={handleSeek}
                        className="flex-1 h-1 bg-gray-700 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:rounded-full"
                    />
                    <span className="text-xs text-gray-400 w-10 text-right">{formatTime(duration)}</span>
                </div>

                {/* Buttons */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => skip(-10)}
                            className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800"
                            title="Back 10s"
                        >
                            <SkipBack className="w-5 h-5" />
                        </button>

                        <button
                            onClick={togglePlay}
                            className="p-3 bg-white text-gray-900 rounded-full hover:bg-gray-200"
                        >
                            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
                        </button>

                        <button
                            onClick={() => skip(10)}
                            className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800"
                            title="Forward 10s"
                        >
                            <SkipForward className="w-5 h-5" />
                        </button>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* Volume */}
                        <div className="flex items-center gap-2">
                            <button
                                onClick={toggleMute}
                                className="p-2 text-gray-400 hover:text-white"
                            >
                                {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                            </button>
                            <input
                                type="range"
                                min={0}
                                max={1}
                                step={0.1}
                                value={isMuted ? 0 : volume}
                                onChange={handleVolumeChange}
                                className="w-20 h-1 bg-gray-700 rounded-full appearance-none cursor-pointer"
                            />
                        </div>

                        {onDownload && (
                            <button
                                onClick={onDownload}
                                className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800"
                                title="Download"
                            >
                                <Download className="w-5 h-5" />
                            </button>
                        )}

                        <button
                            onClick={toggleFullscreen}
                            className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800"
                            title="Fullscreen"
                        >
                            <Maximize2 className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Call Info */}
                <div className="pt-2 border-t border-gray-800 flex items-center justify-between text-sm">
                    <div className="text-gray-400">
                        {participantName && <span className="text-white">{participantName}</span>}
                        {participantName && ' • '}
                        {new Date(callDate).toLocaleDateString()}
                    </div>
                    <span className="text-gray-500 text-xs">ID: {callId.slice(-8)}</span>
                </div>
            </div>
        </div>
    );
}
