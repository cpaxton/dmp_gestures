#!/usr/bin/python
"""
Created on 13/08/14

@author: Sammy Pfeiffer
@email: sammypfeiffer@gmail.com


"""

import rospy
import rosbag
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState
from moveit_msgs.srv import GetPositionIKRequest, GetPositionIKResponse, GetPositionIK
from moveit_msgs.msg import MoveItErrorCodes
from actionlib import SimpleActionClient, GoalStatus
from play_motion_msgs.msg import PlayMotionAction, PlayMotionGoal, PlayMotionResult
from helper_functions import moveit_error_dict, goal_status_dict
from dmp_training import RecordFromPlayMotion
from dmp_generation import gestureGeneration
from dmp_execution import gestureExecution
from moveit_msgs.msg import DisplayTrajectory

from dmp_generation import dmpPlanTrajectoryPlotter

DEFAULT_IK_SERVICE = "/compute_ik"
DEFAULT_JOINT_STATES = "/joint_states"
PLAY_MOTION_AS = "/play_motion"



if __name__ == '__main__':
    rospy.init_node("test_visualize")
    rospy.loginfo("Initializing test.")
    motion = "wave"
    pub = rospy.Publisher('/move_group/display_planned_path', DisplayTrajectory)
    gG = gestureGeneration()
    joint_names = ['arm_right_1_joint', 'arm_right_2_joint', 'arm_right_3_joint',
                           'arm_right_4_joint', 'arm_right_5_joint', 'arm_right_6_joint',
                           'arm_right_7_joint']
    
    if gG.loadGestureYAML(motion +".bag.yaml") == None:
        print "COULDNT LOAD GESTURE FROM YAML, recalculating"
        # If the gesture does not exist
        gesture_dict = gG.loadGestureFromBagJointStates(motion +".bag", joint_names) # TODO: get from the gesture name the joints
    # Now given a gesture loaded in the DMP server, let's ask for a new plan... from the original points so it should be 
    else:
        print "Loading gesture from yaml"
        gesture_dict = gG.loadGestureYAML(motion +".bag.yaml")
    # almost equal to the trained one
    rospy.loginfo("Got gesture:\n" + str(gesture_dict))
#     Looks like:
#             gesture_dict = {"name": name,
#                         "joints" : joints,
#                         "initial_pose" : initial_pose,
#                         "final_pose" : final_pose,
#                         "computed_dmp" : computed_dmp}
    rospy.loginfo("gesture_dict['duration] == " + str(gesture_dict["duration"]))
    plan = gG.getPlan(gesture_dict["initial_pose"], gesture_dict["final_pose"], tau=gesture_dict["duration"], dt=0.05) #, seg_length=int(gesture_dict["duration"]))
    rospy.loginfo("Got plan:\n" + str(plan))
    
    rospy.loginfo("dumping plan to yaml")
    stream = file(motion + "_plan.yaml", "w")
    import yaml
    yaml.dump(plan, stream)
    
    ge = gestureExecution()
    traj = ge.displayTrajFromPlan(plan, joint_names, gesture_dict["initial_pose"])
    rospy.loginfo("Traj is: ")
    rospy.loginfo(str(traj))
    

    rospy.loginfo("Publishing  traj")
    pub.publish(traj)
    rospy.loginfo("Published traj")
    
    dp = dmpPlanTrajectoryPlotter()
    plot = dp.planToPlot(plan, joint_names)
    plot.show()
    
    robot_traj = ge.robotTrajectoryFromPlan(plan, joint_names)
    rospy.loginfo("Sending trajectoryyy!")
    ge.sendTrajectory(robot_traj, True)
    