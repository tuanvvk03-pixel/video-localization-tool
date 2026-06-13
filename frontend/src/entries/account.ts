// Build entry → ../desktop/static/next/account.js (router mount/unmount).
import Account from "../screens/account/Account.svelte";
import { screenFromComponent } from "../lib/screen";

const screen = screenFromComponent(Account);

export const mount = screen.mount;
export const unmount = screen.unmount;
