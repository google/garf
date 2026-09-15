package testenv

import (
	"fmt"
	"net"
	"os"
	"os/exec"
	"sync"
	"time"
)

var (
	serverAddr string
	once       sync.Once
	cmd        *exec.Cmd
)

func GetConnection() (string, func()) {

	var shutdownFn func()
	once.Do(func() {
		listener, err := net.Listen("tcp", "127.0.0.1:0")
		if err != nil {
			fmt.Printf("Failed to find free port: %v\n", err)
			return
		}

		port := listener.Addr().(*net.TCPAddr).Port
		serverAddr = fmt.Sprintf("127.0.0.1:%d", port)
		listener.Close()

		pythonBin := os.Getenv("GARF_GRPC_SERVER_BIN")
		cmd = exec.Command(pythonBin, "-m", "garf.executors.entrypoints.grpc_server", fmt.Sprintf("--port=%d", port))
		fmt.Println(cmd)
		if err := cmd.Start(); err != nil {
			fmt.Printf("Failed to start python server: %v\n", err)
			return
		}

		shutdownFn = func() {
			if cmd.Process != nil {
				_ = cmd.Process.Kill()
			}
		}
	})
	n := 2
	time.Sleep(time.Duration(n) * time.Second)
	return serverAddr, shutdownFn
}

func Teardown() {
	if cmd != nil && cmd.Process != nil {
		_ = cmd.Process.Kill()
		_, _ = cmd.Process.Wait()
	}

}
