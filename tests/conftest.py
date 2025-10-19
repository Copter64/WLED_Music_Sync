"""Test configuration and fixtures"""
import pytest
import os
import tempfile
import yaml

@pytest.fixture
def sample_timings():
    """Create a temporary timings.yml file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump({
            'songs': {
                'test.mp3': [
                    {
                        'time': 0.0,
                        'controllers': {
                            'group': {
                                'controllers': ['sword1', 'sword2'],
                                'preset': 1
                            }
                        }
                    }
                ]
            }
        }, f)
        return f.name

@pytest.fixture
def mock_env(monkeypatch):
    """Setup mock environment variables"""
    monkeypatch.setenv('WLED_CONTROLLERS', 'sword1=http://192.168.1.186,sword2=http://192.168.1.187')
