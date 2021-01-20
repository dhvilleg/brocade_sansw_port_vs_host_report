# Brocade_sansw_port_vs_host_report

This script helps to SAN Admins get a "port vs hosts" report from brocade san directors.

The final report is something like this:

|date|sansw name|index|slot|port|address|media|speed|status|proto|port_type|WWN/ISL/NPIV|hosts
|-|-|-|-|-|-|-|-|-|-|-|-|-|
|2021-01-17 00:00:02|sansw_name1|0|1|0|0b0000|id|8G|Online|FC|F-Port|21:XX:XX:XX:XX:XX:XX:XX|ALI_HOSNAME_LIB|
|2021-01-17 00:00:02|sansw_name2|1|1|1|0b0100|id|8G|Online|FC|E-Port|10:XX:XX:XX:XX:XX:XX:XX "c7002-sw5" (downstream)|
|2021-01-17 00:00:02|sansw_name3|2|1|2|0b0200|id|8G|Online|FC|F-Port|1 N Port + 7 NPIV public|None None None ALI_HOST6_fcs8 ALI_HOST_fcs8 ALI_HOST8_fc0 None None|
|2021-01-17 00:00:02|sansw_name1|4|1|4|0b0400|id|8G|Online|FC|F-Port|50:XX:XX:XX:XX:XX:XX:XX|ALI_IBM_STG01_FO_I0332_E4S4P3|
|2021-01-17 00:00:02|sansw_name2|5|1|5|0b0500|id|8G|Online|FC|F-Port|1 N Port + 4 NPIV public|None None ALI_OTHERHOST_fcs6 ALI_ANOTHERHOST_fcs4 None|
|2021-01-17 00:00:02|sansw_name3|6|1|6|0b0600|id|8G|Online|FC|F-Port|10:XX:XX:XX:XX:XX:XX:XX|None|
|...|...|...|...|...|...|...|...|...|...|...|...|...|
