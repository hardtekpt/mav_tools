cmake_minimum_required(VERSION 3.0.2)
project(mav_tools)

find_package(catkin REQUIRED COMPONENTS
  rospy
  mavros_msgs
)

catkin_package(
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)
