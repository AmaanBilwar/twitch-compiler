"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

type LoadingState = 'idle' | 'selecting' | 'downloading' | 'compiling';

export default function Home() {
  const [username, setUsername] = useState("");
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [clipCount, setClipCount] = useState(10);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) {
      toast.error("Please enter a username");
      return;
    }

    setLoadingState('selecting');
    try {
      const formData = new FormData();
      formData.append("username", username);
      formData.append("clipCount", clipCount.toString());

      // First request to collect and download clips
      setLoadingState('downloading');
      const response = await fetch("http://localhost:5000/collect-clips", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to collect clips");
      }

      // Second request to concatenate clips
      setLoadingState('compiling');
      const concatResponse = await fetch("http://localhost:5000/concatenate-clips", {
        method: "POST",
        body: formData,
      });

      const concatData = await concatResponse.json();

      if (!concatResponse.ok) {
        throw new Error(concatData.error || "Failed to compile clips");
      }

      toast.success(concatData.message);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "An error occurred");
    } finally {
      setLoadingState('idle');
    }
  };

  const getLoadingText = () => {
    switch (loadingState) {
      case 'selecting':
        return "Selecting most watched clips...";
      case 'downloading':
        return "Downloading clips...";
      case 'compiling':
        return "Making a compiled video...";
      default:
        return "Make Compilation";
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-4">
      <div className="text-center mb-6">
        <h2 className="text-xl font-semibold text-gray-800">Clips sorted by "Most Viewed"</h2>
        <Badge className="bg-gradient-to-r from-purple-200 to-pink-200 text-purple-600 gradient-border">More filters coming soon</Badge>
      </div>
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">Twitch Clip Collector</CardTitle>
          <CardDescription className="text-center">
            Enter a Twitch username to collect and download their clips
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Input
                type="text"
                placeholder="Enter Twitch username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full"
                disabled={loadingState !== 'idle'}
              />
              <Input
                type="number"
                placeholder="Number of clips to download"
                value={clipCount}
                onChange={(e) => setClipCount(parseInt(e.target.value) || 10)}
                className="w-full"
                min={1}
                max={100}
                disabled={loadingState !== 'idle'}
              />
            </div>
            <Button
              type="submit"
              className="w-full"
              disabled={loadingState !== 'idle'}
            >
              {getLoadingText()}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
