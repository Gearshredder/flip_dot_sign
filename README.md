# flip_dot_sign

This is a flipdot sign controller using an esp32. It currently uses the original sink drivers. All of this is parallel, using one i/o for each pin.

#### Todo
- [ ] create a multiplexer with i2c to control each of the bits to set the dot. write/erase will be an i/o connected to the controller still.
- [ ] create a webserver that works.
- [ ] organize the files used for this project. There are too many different versions.