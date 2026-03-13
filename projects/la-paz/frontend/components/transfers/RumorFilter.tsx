"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

interface RumorFilterProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedLeague: string;
  onLeagueChange: (league: string) => void;
}

const leagues = ["전체", "EPL", "La Liga", "Serie A", "Bundesliga", "Ligue 1"];

export default function RumorFilter({
  searchQuery,
  onSearchChange,
  selectedLeague,
  onLeagueChange,
}: RumorFilterProps) {
  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
        <Input
          placeholder="선수 또는 팀 검색..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        {leagues.map((league) => (
          <Button
            key={league}
            variant={selectedLeague === league ? "default" : "outline"}
            size="sm"
            className="cursor-pointer"
            onClick={() => onLeagueChange(league)}
          >
            {league}
          </Button>
        ))}
      </div>
    </div>
  );
}
