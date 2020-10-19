import {ServerData} from "./types";

export default class Ctrl {

  constructor(readonly data: ServerData, readonly redraw: () => void) {
  }
}
