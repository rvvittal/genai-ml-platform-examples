export async function getAudioDevices() {
  console.log('getting audio devices');
  const devices: MediaDeviceInfo[] =
    await navigator.mediaDevices.enumerateDevices();
  const microphones = devices.filter((device: MediaDeviceInfo) => {
    return (
      device.kind === 'audioinput' &&
      device.deviceId !== '' &&
      device.label !== ''
    );
  });
  const speakers = devices.filter((device: MediaDeviceInfo) => {
    return (
      device.kind === 'audiooutput' &&
      device.deviceId !== '' &&
      device.label !== ''
    );
  });
  return {
    input: microphones,
    output: speakers,
  };
}

export async function askPermission() {
  return await navigator.mediaDevices
    .getUserMedia({ audio: true, video: false })
    .then((stream) => {
      return true;
    })
    // If there is an error, we can't get access to the mic
    .catch((err) => {
      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        return false;
      } else {
        throw new Error('Unexpected error getting microphone access');
      }
    });
}

export async function getCurrentPermissions() {
  let permissionState: PermissionState = 'prompt';

  if (navigator?.permissions) {
    await navigator.permissions
      ?.query({ name: 'microphone' })
      .then((result) => {
        permissionState = result.state;
      })
      .catch((err) => {
        if (err) {
          console.log(err);
        }
        console.log('error with permission query');
      });
  }

  return permissionState;
}

export function getDeviceById(deviceId: string) {
  return navigator.mediaDevices.getUserMedia({
    audio: { deviceId: { exact: deviceId } },
  });
}
