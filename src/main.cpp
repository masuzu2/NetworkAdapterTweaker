#include "gui.h"

int WINAPI wWinMain(HINSTANCE hInst, HINSTANCE, LPWSTR, int) {
    InitApp(hInst);
    return RunMessageLoop();
}
