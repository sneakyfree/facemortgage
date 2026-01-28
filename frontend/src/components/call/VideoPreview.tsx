'use client';

import { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, RotateCcw } from 'lucide-react';

interface VideoPreviewProps {
    videoUrl: string;
    posterUrl?: string;
    professional: {
        name: string;
        title?: string;
    };
    onCallNow?: () => void;
    className?: string;
}

export function VideoPreview({
    videoUrl,
    posterUrl,
    professional,
    onCallNow,
    className = '',
}: VideoPreviewProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isMuted, setIsMuted] = useState(true);
    const [progress, setProgress] = useState(0);
    const [duration, setDuration] = useState(0);
    const [showControls, setShowControls] = useState(true);
    const [hasEnded, setHasEnded] = useState(false);

    useEffect(() => {
        const video = videoRef.current;
        if (!video) return;

        const handleTimeUpdate = () => {
            setProgress((video.currentTime / video.duration) * 100);
        };

        const handleLoadedMetadata = () => {
            setDuration(video.duration);
        };

        const handleEnded = () => {
            setIsPlaying(false);
            setHasEnded(true);
        };

        video.addEventListener('timeupdate', handleTimeUpdate);
        video.addEventListener('loadedmetadata', handleLoadedMetadata);
        video.addEventListener('ended', handleEnded);

        return () => {
            video.removeEventListener('timeupdate', handleTimeUpdate);
            video.removeEventListener('loadedmetadata', handleLoadedMetadata);
            video.removeEventListener('ended', handleEnded);
        };
    }, []);

    const togglePlay = () => {
        const video = videoRef.current;
        if (!video) return;

        if (isPlaying) {
            video.pause();
        } else {
            video.play();
            setHasEnded(false);
        }
        setIsPlaying(!isPlaying);
    };

    const toggleMute = () => {
        const video = videoRef.current;
        if (!video) return;
        video.muted = !isMuted;
        setIsMuted(!isMuted);
    };

    const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
        const video = videoRef.current;
        if (!video) return;

        const rect = e.currentTarget.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        video.currentTime = percent * video.duration;
    };

    const restart = () => {
        const video = videoRef.current;
        if (!video) return;
        video.currentTime = 0;
        video.play();
        setIsPlaying(true);
        setHasEnded(false);
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const toggleFullscreen = () => {
        const video = videoRef.current;
        if (!video) return;
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            video.requestFullscreen();
        }
    };

    return (
        <div
            className={`relative rounded-2xl overflow-hidden bg-gray-900 group ${className}`}
            onMouseEnter={() => setShowControls(true)}
            onMouseLeave={() => !isPlaying && setShowControls(true)}
        >
            <video
                ref={videoRef}
                src={videoUrl}
                poster={posterUrl}
                muted={isMuted}
                playsInline
                className="w-full aspect-video object-cover"
                onClick={togglePlay}
            />

            {/* Overlay gradient */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />

            {/* Professional info */}
            <div className="absolute bottom-0 left-0 right-0 p-4">
                <div className="flex items-end justify-between">
                    <div className="text-white">
                        <p className="font-semibold text-lg">{professional.name}</p>
                        {professional.title && (
                            <p className="text-sm text-white/80">{professional.title}</p>
                        )}
                    </div>
                    {onCallNow && (
                        <button
                            onClick={onCallNow}
                            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 font-medium flex items-center gap-2"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            Call Now
                        </button>
                    )}
                </div>
            </div>

            {/* Play/Pause overlay */}
            {(!isPlaying || hasEnded) && (
                <div className="absolute inset-0 flex items-center justify-center">
                    <button
                        onClick={hasEnded ? restart : togglePlay}
                        className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-white/30 transition-colors"
                    >
                        {hasEnded ? (
                            <RotateCcw className="w-8 h-8 text-white" />
                        ) : (
                            <Play className="w-8 h-8 text-white ml-1" />
                        )}
                    </button>
                </div>
            )}

            {/* Controls bar */}
            <div
                className={`absolute bottom-16 left-0 right-0 px-4 transition-opacity ${showControls || !isPlaying ? 'opacity-100' : 'opacity-0'
                    }`}
            >
                {/* Progress bar */}
                <div
                    className="h-1 bg-white/30 rounded-full cursor-pointer mb-3"
                    onClick={handleSeek}
                >
                    <div
                        className="h-full bg-white rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                    />
                </div>

                {/* Control buttons */}
                <div className="flex items-center justify-between text-white">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={togglePlay}
                            className="hover:text-white/80 transition-colors"
                            aria-label={isPlaying ? 'Pause' : 'Play'}
                        >
                            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                        </button>
                        <button
                            onClick={toggleMute}
                            className="hover:text-white/80 transition-colors"
                            aria-label={isMuted ? 'Unmute' : 'Mute'}
                        >
                            {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                        </button>
                        <span className="text-sm text-white/80">
                            {formatTime(videoRef.current?.currentTime || 0)} / {formatTime(duration)}
                        </span>
                    </div>
                    <button
                        onClick={toggleFullscreen}
                        className="hover:text-white/80 transition-colors"
                        aria-label="Fullscreen"
                    >
                        <Maximize className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    );
}
