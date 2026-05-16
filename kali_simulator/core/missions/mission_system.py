"""
Mission system for Kali Linux Simulator.
Provides gamified hacking challenges inspired by Grey Hack.
"""

import random
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MissionDifficulty(Enum):
    """Mission difficulty levels."""
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    EXPERT = "Expert"
    LEGENDARY = "Legendary"


class MissionType(Enum):
    """Types of missions."""
    RECONNAISSANCE = "Reconnaissance"
    EXPLOITATION = "Exploitation"
    CRACKING = "Cracking"
    EXFILTRATION = "Exfiltration"
    DEFENSE = "Defense"
    CTF = "CTF"


@dataclass
class MissionObjective:
    """Represents a single mission objective."""
    id: str
    description: str
    completed: bool = False
    hints: List[str] = field(default_factory=list)
    
    def complete(self):
        self.completed = True


@dataclass
class MissionReward:
    """Represents mission rewards."""
    money: int = 0
    reputation: int = 0
    experience: int = 0
    items: List[str] = field(default_factory=list)
    unlocks: List[str] = field(default_factory=list)


@dataclass
class Mission:
    """Represents a hacking mission."""
    id: str
    title: str
    description: str
    type: MissionType
    difficulty: MissionDifficulty
    objectives: List[MissionObjective]
    reward: MissionReward
    target_ip: str = ""
    completed: bool = False
    failed: bool = False
    progress: float = 0.0
    
    def update_progress(self):
        if not self.objectives:
            self.progress = 0.0
            return
        completed = sum(1 for obj in self.objectives if obj.completed)
        self.progress = completed / len(self.objectives)
        if self.progress == 1.0:
            self.completed = True


@dataclass
class PlayerProfile:
    """Player profile with stats and progression."""
    username: str
    level: int = 1
    experience: int = 0
    money: int = 1000
    reputation: int = 0
    completed_missions: List[str] = field(default_factory=list)
    skills: Dict[str, int] = field(default_factory=dict)
    inventory: List[str] = field(default_factory=list)
    unlocked_tools: List[str] = field(default_factory=list)
    
    DEFAULT_SKILLS = {
        'networking': 0,
        'exploitation': 0,
        'cracking': 0,
        'web_security': 0,
    }
    
    def __post_init__(self):
        if not self.skills:
            self.skills = self.DEFAULT_SKILLS.copy()
    
    def add_experience(self, amount: int):
        self.experience += amount
        xp_needed = self.level * 1000
        while self.experience >= xp_needed:
            self.experience -= xp_needed
            self.level += 1
            xp_needed = self.level * 1000
    
    def add_money(self, amount: int):
        self.money += amount
    
    def improve_skill(self, skill: str, amount: int = 1):
        if skill in self.skills:
            self.skills[skill] += amount
    
    def to_dict(self) -> Dict:
        return {
            'username': self.username,
            'level': self.level,
            'experience': self.experience,
            'money': self.money,
            'reputation': self.reputation,
            'completed_missions': self.completed_missions,
            'skills': self.skills,
            'inventory': self.inventory,
            'unlocked_tools': self.unlocked_tools,
        }


class MissionManager:
    """Manages missions and player progression."""
    
    MISSION_TEMPLATES = [
        {
            'id': 'recon_001',
            'title': 'Network Reconnaissance',
            'description': 'Scan the target network and identify all active hosts.',
            'type': MissionType.RECONNAISSANCE,
            'difficulty': MissionDifficulty.EASY,
            'objectives': [
                {'id': 'obj1', 'description': 'Scan 192.168.1.0/24 network', 'hints': ['Use nmap command']},
                {'id': 'obj2', 'description': 'Identify at least 3 active hosts', 'hints': []},
                {'id': 'obj3', 'description': 'Document open ports', 'hints': ['Use nmap -sV']},
            ],
            'reward': {'money': 500, 'reputation': 50, 'experience': 200},
        },
        {
            'id': 'crack_001',
            'title': 'Password Cracking Challenge',
            'description': 'Crack the provided hash and retrieve the password.',
            'type': MissionType.CRACKING,
            'difficulty': MissionDifficulty.MEDIUM,
            'objectives': [
                {'id': 'obj1', 'description': 'Obtain the hash file', 'hints': ['Check /tmp/hashes.txt']},
                {'id': 'obj2', 'description': 'Identify hash type', 'hints': []},
                {'id': 'obj3', 'description': 'Crack the hash', 'hints': ['Use hashcat or john']},
            ],
            'reward': {'money': 800, 'reputation': 100, 'experience': 400},
        },
        {
            'id': 'exploit_001',
            'title': 'Web Server Exploitation',
            'description': 'Exploit the vulnerable web server and gain access.',
            'type': MissionType.EXPLOITATION,
            'difficulty': MissionDifficulty.HARD,
            'objectives': [
                {'id': 'obj1', 'description': 'Scan target web server', 'hints': []},
                {'id': 'obj2', 'description': 'Identify vulnerability', 'hints': []},
                {'id': 'obj3', 'description': 'Gain remote access', 'hints': []},
                {'id': 'obj4', 'description': 'Extract sensitive data', 'hints': []},
            ],
            'reward': {'money': 1500, 'reputation': 200, 'experience': 800},
        },
    ]
    
    def __init__(self, player: PlayerProfile):
        self.player = player
        self.active_missions: List[Mission] = []
        self.available_missions: List[Mission] = []
        self._load_missions()
    
    def _load_missions(self):
        for template in self.MISSION_TEMPLATES:
            mission = self._create_mission_from_template(template)
            self.available_missions.append(mission)
    
    def _create_mission_from_template(self, template: Dict) -> Mission:
        objectives = [
            MissionObjective(id=obj['id'], description=obj['description'], hints=obj.get('hints', []))
            for obj in template['objectives']
        ]
        reward_data = template['reward']
        reward = MissionReward(
            money=reward_data.get('money', 0),
            reputation=reward_data.get('reputation', 0),
            experience=reward_data.get('experience', 0),
        )
        return Mission(
            id=template['id'],
            title=template['title'],
            description=template['description'],
            type=template['type'],
            difficulty=template['difficulty'],
            objectives=objectives,
            reward=reward,
        )
    
    def get_available_missions(self) -> List[Mission]:
        return [m for m in self.available_missions if not m.completed and not m.failed]
    
    def accept_mission(self, mission_id: str) -> Optional[Mission]:
        for mission in self.available_missions:
            if mission.id == mission_id:
                self.available_missions.remove(mission)
                self.active_missions.append(mission)
                return mission
        return None
    
    def complete_objective(self, mission_id: str, objective_id: str) -> bool:
        for mission in self.active_missions:
            if mission.id == mission_id:
                for obj in mission.objectives:
                    if obj.id == objective_id and not obj.completed:
                        obj.complete()
                        mission.update_progress()
                        if mission.type == MissionType.RECONNAISSANCE:
                            self.player.improve_skill('networking')
                        elif mission.type == MissionType.EXPLOITATION:
                            self.player.improve_skill('exploitation')
                        elif mission.type == MissionType.CRACKING:
                            self.player.improve_skill('cracking')
                        if mission.completed:
                            self._complete_mission(mission)
                        return True
        return False
    
    def _complete_mission(self, mission: Mission):
        self.player.add_money(mission.reward.money)
        self.player.add_experience(mission.reward.experience)
        self.active_missions.remove(mission)
        self.player.completed_missions.append(mission.id)
    
    def get_player_status(self) -> Dict:
        return {
            'username': self.player.username,
            'level': self.player.level,
            'money': self.player.money,
            'reputation': self.player.reputation,
            'active_missions': len(self.active_missions),
            'completed_missions': len(self.player.completed_missions),
        }


def create_new_player(username: str) -> PlayerProfile:
    return PlayerProfile(username=username)


def get_mission_manager(player: PlayerProfile = None) -> MissionManager:
    global _mission_manager, _current_player
    if player is not None:
        _current_player = player
        _mission_manager = MissionManager(player)
    return _mission_manager


_mission_manager: Optional[MissionManager] = None
_current_player: Optional[PlayerProfile] = None
