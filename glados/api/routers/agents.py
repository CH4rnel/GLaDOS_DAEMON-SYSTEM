# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

import os
import re
import yaml
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, SecretStr

from glados.api.dependencies import get_registry, get_guardian
from glados.llm.factory import LLMProviderFactory
from glados.llm.models import AgentProfile, ProviderType
from glados.security.guardian import GuardianGate

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

class AgentActivationRequest(BaseModel):
    api_key: str

def _parse_api_key(raw_key: str) -> str:
    key = raw_key.strip()
    if key.lower().startswith("export "):
        key = key[7:].strip()
    if "=" in key:
        key = key.split("=", 1)[1].strip()
    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
        key = key[1:-1]
    return key.strip()

def _load_all_agent_configs() -> list[dict]:
    config_path = Path("configs/agents.yaml")
    if not config_path.exists():
        return []
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("agents", [])

@router.get("/")
async def list_agents(registry = Depends(get_registry)):
    all_configs = _load_all_agent_configs()
    registered_agents = {p.agent_id: p for p in registry.list_all()}
    
    result = []
    for config in all_configs:
        agent_id = config.get("agent_id")
        is_active = agent_id in registered_agents
        result.append({
            "agent_id": agent_id,
            "display_name": config.get("display_name", agent_id),
            "provider": config.get("provider"),
            "model": config.get("model"),
            "is_active": is_active,
            "requires_api_key": bool(config.get("api_key")) or "${" in str(config.get("api_key", ""))
        })
    return result

@router.post("/{agent_id}/activate")
async def activate_agent(
    agent_id: str,
    request_data: AgentActivationRequest,
    request: Request,
    registry = Depends(get_registry),
    guardian: GuardianGate = Depends(get_guardian)
):
    config_path = Path("configs/agents.yaml")
    if not config_path.exists():
        guardian.log_audit("DENY", f"agent.activate.{agent_id}", "Config file missing")
        raise HTTPException(status_code=500, detail="Configuration file missing")
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    agent_config = next((a for a in data.get("agents", []) if a["agent_id"] == agent_id), None)
    if not agent_config:
        guardian.log_audit("DENY", f"agent.activate.{agent_id}", "Agent not found in config")
        raise HTTPException(status_code=404, detail="Agent configuration not found")

    try:
        registry.get(agent_id)
        guardian.log_audit("ALLOW", f"agent.activate.{agent_id}", "Agent already active")
        return {"status": "already_active", "agent_id": agent_id}
    except Exception:
        pass

    clean_api_key = _parse_api_key(request_data.api_key)

    profile = AgentProfile(
        agent_id=agent_config["agent_id"],
        display_name=agent_config.get("display_name", agent_id),
        provider=ProviderType(agent_config["provider"]),
        model=agent_config["model"],
        base_url=os.environ.get(f"{agent_config['provider'].upper()}_BASE_URL") or agent_config.get("base_url"),
        api_key=SecretStr(clean_api_key),
        system_prompt=agent_config.get("system_prompt", ""),
        temperature=agent_config.get("temperature", 0.7),
        max_tokens=agent_config.get("max_tokens"),
        tags=agent_config.get("tags", []),
        is_active=True,
    )

    try:
        provider = LLMProviderFactory.create_provider(profile)
    except ValueError as e:
        guardian.log_audit("DENY", f"agent.activate.{agent_id}", str(e))
        raise HTTPException(status_code=400, detail=str(e))

    try:
        is_valid = await provider.validate_api_key()
    except Exception as e:
        guardian.log_audit("DENY", f"agent.activate.{agent_id}", f"Validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail="API key validation failed")

    if not is_valid:
        guardian.log_audit("DENY", f"agent.activate.{agent_id}", "Invalid API key")
        raise HTTPException(status_code=401, detail="Invalid API key")

    registry.register(profile, provider)
    guardian.log_audit("ALLOW", f"agent.activate.{agent_id}", "Provider registered successfully")
    
    return {"status": "activated", "agent_id": agent_id, "provider": profile.provider.value}