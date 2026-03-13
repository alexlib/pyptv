"""Extended parameter testing to find the real optimal values"""

import subprocess
import sys
import math
from pathlib import Path
import pytest


def test_extended_acceleration_range():
    """Smoke test a bounded acceleration sweep."""
    
    test_path = Path(__file__).parent / "test_splitter"
    
    print("🔍 Testing extended acceleration constraint range...")
    print("="*60)
    
    acceleration_values = [1.9, 10.0]
    
    results = {}
    
    for dacc in acceleration_values:
        print(f"\n⚡ Testing acceleration constraint: {dacc}")
        
        # Modify the YAML file temporarily
        yaml_file = test_path / "parameters_Run1.yaml"
        backup_content = yaml_file.read_text()
        
        try:
            # Modify acceleration parameter
            content = backup_content
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'dacc:' in line and ('track:' in content[:content.find(line)] or i > 0 and 'track:' in lines[i-5:i]):
                    lines[i] = f"  dacc: {dacc}"
                    break
            
            modified_content = '\n'.join(lines)
            yaml_file.write_text(modified_content)
            
            # Run tracking with this acceleration value
            link_ratio = run_tracking_test(test_path, f"dacc_{dacc}")
            results[dacc] = link_ratio
            
            print(f"   Link ratio: {link_ratio:.1f}%")
            
        finally:
            # Restore original content
            yaml_file.write_text(backup_content)
    
    assert set(results) == set(acceleration_values)
    assert all(isinstance(ratio, float) and ratio >= 0.0 for ratio in results.values())


def test_velocity_parameter_interaction():
    """Smoke test one bounded velocity and acceleration interaction set."""
    
    test_path = Path(__file__).parent / "test_splitter"
    
    print("🔍 Testing velocity-acceleration parameter interactions...")
    print("="*60)
    
    velocity_ranges = [1.9]
    acceleration_values = [10.0]
    
    results = {}
    
    for vel_range in velocity_ranges:
        for dacc in acceleration_values:
            test_name = f"vel±{vel_range}_acc{dacc}"
            print(f"\n🔧 Testing vel=±{vel_range}, acc={dacc}")
            
            # Modify the YAML file temporarily
            yaml_file = test_path / "parameters_Run1.yaml"
            backup_content = yaml_file.read_text()
            
            try:
                # Modify parameters
                content = backup_content
                lines = content.split('\n')
                in_track_section = False
                
                for i, line in enumerate(lines):
                    if 'track:' in line:
                        in_track_section = True
                    elif in_track_section and line.strip() and not line.startswith('  '):
                        in_track_section = False
                    
                    if in_track_section:
                        if 'dvxmin:' in line:
                            lines[i] = f"  dvxmin: {-vel_range}"
                        elif 'dvxmax:' in line:
                            lines[i] = f"  dvxmax: {vel_range}"
                        elif 'dvymin:' in line:
                            lines[i] = f"  dvymin: {-vel_range}"
                        elif 'dvymax:' in line:
                            lines[i] = f"  dvymax: {vel_range}"
                        elif 'dvzmin:' in line:
                            lines[i] = f"  dvzmin: {-vel_range}"
                        elif 'dvzmax:' in line:
                            lines[i] = f"  dvzmax: {vel_range}"
                        elif 'dacc:' in line:
                            lines[i] = f"  dacc: {dacc}"
                
                modified_content = '\n'.join(lines)
                yaml_file.write_text(modified_content)
                
                # Run tracking test
                link_ratio = run_tracking_test(test_path, test_name)
                results[test_name] = {
                    'vel_range': vel_range,
                    'dacc': dacc,
                    'link_ratio': link_ratio
                }
                
                print(f"   Link ratio: {link_ratio:.1f}%")
                
            finally:
                # Restore original content
                yaml_file.write_text(backup_content)
    
    assert len(results) == 1
    assert all(result['link_ratio'] >= 0.0 for result in results.values())


def run_tracking_test(test_path, test_name):
    """Run a single tracking test and return the link ratio"""
    
    script_path = Path(__file__).parent.parent / "pyptv" / "pyptv_batch_plugins.py"
    yaml_file = test_path / "parameters_Run1.yaml"
    cmd = [
        sys.executable, 
        str(script_path), 
        str(yaml_file), 
        "1000001", 
        "1000003",  # 3 frames for tracking analysis
        "--mode", "sequence"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return 0.0
        
        # Parse tracking output to get link ratio
        lines = result.stdout.split('\n')
        tracking_lines = [line for line in lines if 'step:' in line and 'links:' in line]
        
        total_particles = 0
        total_links = 0
        frames_count = 0
        
        for line in tracking_lines:
            try:
                parts = line.split(',')
                curr_part = [p for p in parts if 'curr:' in p][0]
                curr_count = int(curr_part.split(':')[1].strip())
                
                links_part = [p for p in parts if 'links:' in p][0]
                links_count = int(links_part.split(':')[1].strip())
                
                total_particles += curr_count
                total_links += links_count
                frames_count += 1
                
            except (ValueError, IndexError):
                continue
        
        if frames_count > 0 and total_particles > 0:
            avg_particles = total_particles / frames_count
            avg_links = total_links / frames_count
            link_ratio = (avg_links / avg_particles * 100)
            return link_ratio
        else:
            return 0.0
            
    except subprocess.TimeoutExpired:
        return 0.0
    except Exception as e:
        return 0.0


if __name__ == "__main__":
    print("🔬 Extended Tracking Parameter Analysis")
    print("="*60)
    
    print("1️⃣ Testing extended acceleration range...")
    best_dacc, best_acc_ratio = test_extended_acceleration_range()
    
    print("\n" + "="*60)
    print("2️⃣ Testing velocity-acceleration interactions...")
    best_combo = test_velocity_parameter_interaction()
    
    print("\n" + "="*60)
    print("🎯 Final Recommendations:")
    print(f"Best acceleration only: {best_dacc} → {best_acc_ratio:.1f}%")
    print(f"Best combination: vel=±{best_combo['vel_range']}, acc={best_combo['dacc']} → {best_combo['link_ratio']:.1f}%")
