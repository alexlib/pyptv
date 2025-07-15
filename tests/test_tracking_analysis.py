"""Detailed tracking performance analysis"""

import subprocess
import sys
import math
from pathlib import Path
import pytest


def analyze_tracking_performance():
    """Analyze tracking performance with different parameter settings"""
    
    test_path = Path(__file__).parent / "test_splitter"
    script_path = Path(__file__).parent.parent / "pyptv" / "pyptv_batch_plugins.py"
    
    if not test_path.exists() or not script_path.exists():
        print("❌ Required files not found")
        return
    
    # Run batch with current parameters
    cmd = [
        sys.executable, 
        str(script_path), 
        str(test_path), 
        "1000001", 
        "1000003",  # 3 frames for better tracking analysis
        "--sequence", "ext_sequence_splitter",
        "--tracking", "ext_tracker_splitter"
    ]
    
    print("🔍 Running tracking analysis...")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    
    if result.returncode != 0:
        print(f"❌ Run failed: {result.stderr}")
        return
    
    print("📊 Tracking Results Analysis:")
    print("="*50)
    
    # Parse tracking output
    lines = result.stdout.split('\n')
    
    # Find sequence processing output
    sequence_lines = [line for line in lines if 'correspondences' in line]
    for line in sequence_lines:
        print(f"📈 {line}")
    
    print("\n🔗 Tracking Performance:")
    # Find tracking output lines
    tracking_lines = [line for line in lines if 'step:' in line and 'links:' in line]
    
    total_particles = 0
    total_links = 0
    frames_count = 0
    
    for line in tracking_lines:
        print(f"📊 {line}")
        
        # Parse numbers for analysis
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
    
    print("\n📋 Summary:")
    if frames_count > 0:
        avg_particles = total_particles / frames_count
        avg_links = total_links / frames_count
        link_ratio = (avg_links / avg_particles * 100) if avg_particles > 0 else 0
        
        print(f"Average particles per frame: {avg_particles:.1f}")
        print(f"Average links per frame: {avg_links:.1f}")
        print(f"Link ratio: {link_ratio:.1f}%")
        
        # Analysis
        if link_ratio < 20:
            print("⚠️  Low link ratio suggests:")
            print("   - Velocity constraints might be too restrictive")
            print("   - Particle motion might be larger than expected")
            print("   - Time step between frames might be too large")
        elif link_ratio > 50:
            print("✅ Good link ratio indicates healthy tracking")
        else:
            print("🔄 Moderate link ratio - could potentially be improved")
    
    # Check for any error messages
    error_lines = [line for line in lines if 'error' in line.lower() or 'failed' in line.lower()]
    if error_lines:
        print("\n⚠️  Potential Issues:")
        for line in error_lines:
            print(f"   {line}")


def examine_particle_motion():
    """Examine actual particle motion to understand tracking constraints"""
    
    test_path = Path(__file__).parent / "test_splitter"
    
    print("🔍 Examining particle motion characteristics...")
    
    # Check if we have correspondence files from previous runs
    corres_files = list(test_path.glob("*.1000*"))
    
    if corres_files:
        print(f"Found {len(corres_files)} correspondence files")
        
        # Read a few files to analyze particle motion
        for i, corres_file in enumerate(sorted(corres_files)[:3]):
            print(f"\n📄 {corres_file.name}:")
            try:
                with open(corres_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        particle_count = int(lines[0].strip())
                        print(f"   Particles: {particle_count}")
                        
                        # Show first few particle positions
                        for j, line in enumerate(lines[1:6]):  # First 5 particles
                            parts = line.strip().split()
                            if len(parts) >= 7:
                                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                                print(f"   Particle {j+1}: ({x:.2f}, {y:.2f}, {z:.2f})")
            except Exception as e:
                print(f"   Error reading file: {e}")
    else:
        print("No correspondence files found - run sequence processing first")


def check_tracking_parameters():
    """Check current tracking parameters in detail"""
    
    from pyptv.experiment import Experiment
    
    test_path = Path(__file__).parent / "test_splitter"
    
    experiment = Experiment()
    experiment.populate_runs(test_path)
    experiment.setActive(0)
    
    track_params = experiment.parameter_manager.get_parameter('track', {})
    
    if track_params is None:
        print("❌ No tracking parameters found")
        return
    
    print("📋 Current Tracking Parameters:")
    print("="*30)
    for key, value in track_params.items():
        print(f"{key:20}: {value}")
    
    # Calculate velocity range
    required_params = ['dvxmin', 'dvxmax', 'dvymin', 'dvymax', 'dvzmin', 'dvzmax']
    if all(param in track_params for param in required_params):
        vx_range = track_params['dvxmax'] - track_params['dvxmin']
        vy_range = track_params['dvymax'] - track_params['dvymin']
        vz_range = track_params['dvzmax'] - track_params['dvzmin']
        
        print(f"\n📏 Velocity Ranges:")
        print(f"X velocity range: {vx_range} (±{vx_range/2})")
        print(f"Y velocity range: {vy_range} (±{vy_range/2})")
        print(f"Z velocity range: {vz_range} (±{vz_range/2})")
        
        # Check if ranges are reasonable
        total_range = (vx_range + vy_range + vz_range) / 3
        if total_range < 1.0:
            print("⚠️  Velocity ranges might be too restrictive")
        elif total_range > 10.0:
            print("⚠️  Velocity ranges might be too permissive")
        else:
            print("✅ Velocity ranges appear reasonable")


@pytest.mark.skip(reason="Long running tracking analysis test - skip for faster testing")
def test_angle_parameters():
    """Test different angle constraint values to find optimal tracking"""
    
    test_path = Path(__file__).parent / "test_splitter"
    
    print("🔍 Testing different angle constraint values...")
    print("="*50)
    
    # Test different angle values (in radians)
    angle_values = [0.1, 0.2, 0.5, 1.0, 1.57, math.pi]  # 0.1 to π radians
    
    results = {}
    
    for angle in angle_values:
        print(f"\n📐 Testing angle constraint: {angle:.2f} radians ({angle * 180/math.pi:.1f} degrees)")
        
        # Modify the YAML file temporarily
        yaml_file = test_path / "parameters_Run1.yaml"
        backup_content = yaml_file.read_text()
        
        try:
            # Read current content and modify angle parameter
            content = backup_content
            # Replace the angle line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'angle:' in line and 'track:' in content[:content.find(line)]:
                    lines[i] = f"  angle: {angle}"
                    break
            
            modified_content = '\n'.join(lines)
            yaml_file.write_text(modified_content)
            
            # Run tracking with this angle value
            link_ratio = run_tracking_test(test_path, f"angle_{angle:.2f}")
            results[angle] = link_ratio
            
            print(f"   Link ratio: {link_ratio:.1f}%")
            
        finally:
            # Restore original content
            yaml_file.write_text(backup_content)
    
    # Find best angle value
    best_angle = max(results.keys(), key=lambda k: results[k])
    best_ratio = results[best_angle]
    
    print(f"\n🏆 Best angle constraint: {best_angle:.2f} radians ({best_angle * 180/math.pi:.1f} degrees)")
    print(f"   Best link ratio: {best_ratio:.1f}%")
    
    # Show all results
    print(f"\n📊 All angle test results:")
    for angle, ratio in sorted(results.items()):
        marker = "🏆" if angle == best_angle else "  "
        print(f"{marker} {angle:.2f} rad ({angle * 180/math.pi:.1f}°): {ratio:.1f}%")
    
    return best_angle, best_ratio


@pytest.mark.skip(reason="Long running tracking analysis test - skip for faster testing")
def test_acceleration_parameters():
    """Test different acceleration constraint values to find optimal tracking"""
    
    test_path = Path(__file__).parent / "test_splitter"
    
    print("🔍 Testing different acceleration constraint values...")
    print("="*50)
    
    # Test different acceleration values
    acceleration_values = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    
    results = {}
    
    for dacc in acceleration_values:
        print(f"\n⚡ Testing acceleration constraint: {dacc}")
        
        # Modify the YAML file temporarily
        yaml_file = test_path / "parameters_Run1.yaml"
        backup_content = yaml_file.read_text()
        
        try:
            # Read current content and modify acceleration parameter
            content = backup_content
            # Replace the dacc line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'dacc:' in line and 'track:' in content[:content.find(line)]:
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
    
    # Find best acceleration value
    best_dacc = max(results.keys(), key=lambda k: results[k])
    best_ratio = results[best_dacc]
    
    print(f"\n🏆 Best acceleration constraint: {best_dacc}")
    print(f"   Best link ratio: {best_ratio:.1f}%")
    
    # Show all results
    print(f"\n📊 All acceleration test results:")
    for dacc, ratio in sorted(results.items()):
        marker = "🏆" if dacc == best_dacc else "  "
        print(f"{marker} {dacc:4.1f}: {ratio:.1f}%")
    
    return best_dacc, best_ratio


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
            print(f"❌ Test {test_name} failed")
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
        print(f"❌ Test {test_name} timed out")
        return 0.0
    except Exception as e:
        print(f"❌ Test {test_name} error: {e}")
        return 0.0


@pytest.mark.skip(reason="Long running tracking analysis test - skip for faster testing")
def test_combined_optimization():
    """Test combinations of the best angle and acceleration parameters"""
    
    print("🔍 Testing combined parameter optimization...")
    print("="*50)
    
    # First find best individual parameters
    print("1️⃣ Finding best angle parameter...")
    best_angle, angle_ratio = test_angle_parameters()
    
    print("\n2️⃣ Finding best acceleration parameter...")
    best_dacc, dacc_ratio = test_acceleration_parameters()
    
    # Test the combination
    print(f"\n3️⃣ Testing combined parameters...")
    test_path = Path(__file__).parent / "test_splitter"
    yaml_file = test_path / "parameters_Run1.yaml"
    backup_content = yaml_file.read_text()
    
    try:
        # Modify both parameters
        content = backup_content
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if 'angle:' in line and 'track:' in content[:content.find(line)]:
                lines[i] = f"  angle: {best_angle}"
            elif 'dacc:' in line and 'track:' in content[:content.find(line)]:
                lines[i] = f"  dacc: {best_dacc}"
        
        modified_content = '\n'.join(lines)
        yaml_file.write_text(modified_content)
        
        # Run tracking with combined parameters
        combined_ratio = run_tracking_test(test_path, "combined")
        
        print(f"\n📊 Optimization Results:")
        print(f"Best angle alone:        {best_angle:.2f} rad → {angle_ratio:.1f}%")
        print(f"Best acceleration alone: {best_dacc:.1f} → {dacc_ratio:.1f}%")
        print(f"Combined parameters:     {combined_ratio:.1f}%")
        
        if combined_ratio > max(angle_ratio, dacc_ratio):
            print("🎉 Combined parameters show improvement!")
        elif combined_ratio > max(angle_ratio, dacc_ratio) * 0.95:
            print("✅ Combined parameters are competitive")
        else:
            print("⚠️  Combined parameters show degradation")
        
        return best_angle, best_dacc, combined_ratio
        
    finally:
        # Restore original content
        yaml_file.write_text(backup_content)


if __name__ == "__main__":
    print("🔧 Checking current tracking parameters...")
    check_tracking_parameters()
    print("\n" + "="*60 + "\n")
    
    print("📊 Examining particle motion...")
    examine_particle_motion()
    print("\n" + "="*60 + "\n")
    
    print("🎯 Running baseline tracking analysis...")
    analyze_tracking_performance()
    print("\n" + "="*60 + "\n")
    
    print("🔍 Optimizing angle parameters...")
    test_angle_parameters()
    print("\n" + "="*60 + "\n")
    
    print("⚡ Optimizing acceleration parameters...")
    test_acceleration_parameters()
    print("\n" + "="*60 + "\n")
    
    print("🚀 Testing combined optimization...")
    test_combined_optimization()
