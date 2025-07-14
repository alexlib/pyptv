"""Extended parameter testing to find the real optimal values"""

import subprocess
import sys
import math
from pathlib import Path


def test_extended_acceleration_range():
    """Test a much wider range of acceleration values"""
    
    test_path = Path(__file__).parent / "test_splitter"
    
    print("🔍 Testing extended acceleration constraint range...")
    print("="*60)
    
    # Test much wider range including higher values
    acceleration_values = [0.0, 0.5, 1.0, 1.9, 2.0, 5.0, 10.0, 15.0, 20.0, 30.0, 50.0, 100.0]
    
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
    
    # Analyze results
    print(f"\n📊 Extended Acceleration Test Results:")
    print("="*40)
    best_dacc = max(results.keys(), key=lambda k: results[k])
    best_ratio = results[best_dacc]
    
    for dacc, ratio in sorted(results.items()):
        marker = "🏆" if dacc == best_dacc else "  "
        print(f"{marker} {dacc:6.1f}: {ratio:5.1f}%")
    
    print(f"\n🏆 Best acceleration constraint: {best_dacc}")
    print(f"   Best link ratio: {best_ratio:.1f}%")
    
    return best_dacc, best_ratio


def test_velocity_parameter_interaction():
    """Test if velocity constraints are interacting with acceleration"""
    
    test_path = Path(__file__).parent / "test_splitter"
    
    print("🔍 Testing velocity-acceleration parameter interactions...")
    print("="*60)
    
    # Test combinations of velocity ranges and acceleration
    velocity_ranges = [1.9, 3.0, 5.0, 10.0]  # ±range
    acceleration_values = [1.9, 10.0, 20.0, 50.0]
    
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
    
    # Analyze results
    print(f"\n📊 Velocity-Acceleration Interaction Results:")
    print("="*50)
    print("Vel Range | Acceleration | Link Ratio")
    print("-"*50)
    
    best_combo = max(results.keys(), key=lambda k: results[k]['link_ratio'])
    best_result = results[best_combo]
    
    for test_name, result in sorted(results.items(), key=lambda x: (x[1]['vel_range'], x[1]['dacc'])):
        marker = "🏆" if test_name == best_combo else "  "
        vel = result['vel_range']
        acc = result['dacc']
        ratio = result['link_ratio']
        print(f"{marker} ±{vel:4.1f}   |    {acc:6.1f}    |   {ratio:5.1f}%")
    
    print(f"\n🏆 Best combination:")
    print(f"   Velocity range: ±{best_result['vel_range']}")
    print(f"   Acceleration: {best_result['dacc']}")
    print(f"   Link ratio: {best_result['link_ratio']:.1f}%")
    
    return best_result


def run_tracking_test(test_path, test_name):
    """Run a single tracking test and return the link ratio"""
    
    script_path = Path(__file__).parent.parent / "pyptv" / "pyptv_batch_plugins.py"
    
    cmd = [
        sys.executable, 
        str(script_path), 
        str(test_path), 
        "1000001", 
        "1000003",  # 3 frames for tracking analysis
        "--sequence", "ext_sequence_splitter",
        "--tracking", "ext_tracker_splitter"
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
